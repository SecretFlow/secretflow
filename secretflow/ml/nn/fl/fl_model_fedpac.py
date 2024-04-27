#!/usr/bin/env python3
# *_* coding: utf-8 *_*

# Copyright 2022 Ant Group Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import logging
import math
import os
from typing import Callable, Dict, List, Tuple, Union

import numpy as np
import cvxpy as cvx
import torch

from secretflow.data.horizontal import HDataFrame
from secretflow.data.ndarray import FedNdarray
from secretflow.device import PYU, reveal, wait
from secretflow.ml.nn.callbacks.callbacklist import CallbackList
from secretflow.ml.nn.fl.fl_model import FLModel
from secretflow.utils.random import global_random
from secretflow.ml.nn.metrics import Metric, aggregate_metrics


class FLModelFedPAC(FLModel):
    def pairwise(self, data):
        """
        Simple generator of the pairs (x, y) in a tuple such that index x < index y.
        Args:
        data Indexable (including ability to query length) containing the elements
        Returns:
        Generator over the pairs of the elements of 'data'
        """
        n = len(data)
        for i in range(n):
            for j in range(i, n):
                yield (data[i], data[j])

    def classifier_collaboration_weight_compute(
        self, physical_device_type, client_var_list, client_h_list_pyu, **kwargs
    ):
        # device = client_h_list[0].device
        num_cls = client_h_list_pyu[0].data.shape[0]
        d = client_h_list_pyu[0].data.shape[1]
        avg_weight = []
        num_users = len(client_h_list_pyu)
        # client_var_list = [v.data for v in client_var_list_pyu]
        client_h_list = [h.data for h in client_h_list_pyu]
        for i in range(num_users):
            v = torch.tensor(client_var_list, device=physical_device_type)
            h_ref = client_h_list[i]

            dist = torch.zeros((num_users, num_users), device=physical_device_type)
            for j1, j2 in self.pairwise(tuple(range(num_users))):
                h_j1 = client_h_list[j1]
                h_j2 = client_h_list[j2]
                h = torch.zeros((d, d), device=physical_device_type)
                for k in range(num_cls):
                    h += torch.mm(
                        (h_ref[k] - h_j1[k]).reshape(d, 1),
                        (h_ref[k] - h_j2[k]).reshape(1, d),
                    )
                dj12 = torch.trace(h)
                dist[j1][j2] = dj12
                dist[j2][j1] = dj12

            p_matrix = torch.diag(v) + dist
            p_matrix = p_matrix.cpu().numpy()
            evals, evecs = torch.linalg.eig(torch.tensor(p_matrix))
            p_matrix_new = 0

            for i in range(num_users):
                if evals[i].real >= 0.01:
                    real_part_of_evec = evecs[:, i].real.view(num_users, 1)
                    p_matrix_new += evals[i].real * torch.mm(
                        real_part_of_evec, real_part_of_evec.T
                    )

            p_matrix = (
                p_matrix_new.numpy()
                if not np.all(np.linalg.eigvals(p_matrix) >= 0.0)
                else p_matrix
            )

            alpha = 0
            eps = 1e-3
            if np.all(np.linalg.eigvals(p_matrix) >= 0):
                alphav = cvx.Variable(num_users)
                obj = cvx.Minimize(cvx.quad_form(alphav, p_matrix))
                prob = cvx.Problem(obj, [cvx.sum(alphav) == 1.0, alphav >= 0])
                prob.solve()
                alpha = alphav.value
                alpha = [
                    (i) * (i > eps) for i in alpha
                ]  # zero-out small weights (<eps)
                if i == 0:
                    print("({}) Agg Weights of Classifier Head".format(i + 1))
                    print(alpha, "\n")

            else:
                alpha = None  # if no solution for the optimization problem, use local classifier only

            avg_weight.append(alpha)
        return avg_weight

    def fit(
        self,
        x: Union[HDataFrame, FedNdarray, Dict[PYU, str]],
        y: Union[HDataFrame, FedNdarray, str],
        batch_size: Union[int, Dict[PYU, int]] = 32,
        batch_sampling_rate: float = None,
        epochs: int = 1,
        verbose: int = 1,
        callbacks=None,
        validation_data=None,
        shuffle=False,
        class_weight=None,
        sample_weight=None,
        validation_freq=1,
        aggregate_freq=1,
        label_decoder=None,
        max_batch_size=20000,
        prefetch_buffer_size=None,
        sampler_method="batch",
        random_seed=None,
        dp_spent_step_freq=None,
        audit_log_dir=None,
        dataset_builder: Dict[PYU, Callable] = None,
        wait_steps=100,
    ) -> Dict:
        """Horizontal federated training interface

        Args:
            x: feature, FedNdArray, HDataFrame or Dict {PYU: model_path}
            y: label, FedNdArray, HDataFrame or str(column name of label)
            batch_size: Number of samples per gradient update, int or Dict, recommend 64 or more for safety
            batch_sampling_rate: Ratio of sample per batch, float
            epochs: Number of epochs to train the model
            verbose: 0, 1. Verbosity mode
            callbacks: List of `keras.callbacks.Callback` instances.
            validation_data: Data on which to evaluate
            shuffle: whether to shuffle the training data
            class_weight: Dict mapping class indices (integers) to a weight (float)
            sample_weight: weights for the training samples
            validation_freq: specifies how many training epochs to run before a new validation run is performed
            aggregate_freq: Number of steps of aggregation
            label_decoder: Only used for CSV reading, for label preprocess
            max_batch_size: Max limit of batch size
            prefetch_buffer_size: An int specifying the number of feature batches to prefetch for performance improvement. Only for csv reader
            sampler_method: The name of sampler method
            random_seed: Prg seed for shuffling
            dp_spent_step_freq: specifies how many training steps to check the budget of dp
            audit_log_dir: path of audit log dir, checkpoint will be save if audit_log_dir is not None
            dataset_builder: Callable function about hot to build the dataset. must return (dataset, steps_per_epoch)
            wait_steps: A step size to indicate how many concurrent tasks should be waited, which could prevent the stuck of ray when more tasks join (default 100).
        Returns:
            A history object. It's history.global_history attribute is a
            aggregated record of training loss values and metrics, while
            history.local_history attribute is a record of training loss
            values and metrics of each party.
        """
        if not random_seed:
            random_seed = global_random([*self._workers][0], 100000)

        params = locals()
        logging.info(f"FL Train Params: {params}")

        # sanity check
        if self._aggregator is None:
            if self.server_agg_method is None or self.server is None:
                raise Exception(
                    "When aggregator is none, neither the server nor the server_agg_method can be none"
                )
        assert isinstance(validation_freq, int) and validation_freq >= 1
        assert isinstance(aggregate_freq, int) and aggregate_freq >= 1
        if dp_spent_step_freq is not None:
            assert (
                isinstance(dp_spent_step_freq, int) and dp_spent_step_freq >= 1
            ), "dp_spent_step_freq should be a integer and greater than or equal to 1!"

        # build dataset
        if isinstance(x, Dict):
            if validation_data is not None:
                valid_x, valid_y = validation_data, y
            else:
                valid_x, valid_y = None, None

            logging.info("start handling data file.")
            train_steps_per_epoch = self._handle_file(
                x,
                y,
                batch_size=batch_size,
                sampling_rate=batch_sampling_rate,
                shuffle=shuffle,
                random_seed=random_seed,
                epochs=epochs,
                label_decoder=label_decoder,
                max_batch_size=max_batch_size,
                prefetch_buffer_size=prefetch_buffer_size,
                dataset_builder=dataset_builder,
            )
        else:
            assert type(x) == type(y), "x and y must be same data type"
            if isinstance(x, HDataFrame) and isinstance(y, HDataFrame):
                train_x, train_y = x.values, y.values
            else:
                train_x, train_y = x, y

            if validation_data is not None:
                valid_x, valid_y = validation_data[0], validation_data[1]
            else:
                valid_x, valid_y = None, None

            train_steps_per_epoch = self._handle_data(
                train_x,
                train_y,
                sample_weight=sample_weight,
                batch_size=batch_size,
                sampling_rate=batch_sampling_rate,
                shuffle=shuffle,
                random_seed=random_seed,
                epochs=epochs,
                sampler_method=sampler_method,
                dataset_builder=dataset_builder,
            )

        logging.info("dataset handled")
        # setup callback list
        callbacks = CallbackList(
            callbacks=callbacks,
            add_history=True,
            add_progbar=verbose != 0,
            workers=self._workers,
            device_y=None,
            epochs=epochs,
            verbose=verbose,
            steps=train_steps_per_epoch,
        )

        callbacks.on_train_begin()
        model_params = None
        model_params_list = None

        for epoch in range(epochs):
            res = []
            report_list = []
            # do train
            report_list.append(f"epoch: {epoch+1}/{epochs} - ")
            callbacks.on_epoch_begin(epoch=epoch)

            # get v, h, size_label, dataset_size, w_local_keys, sample_num
            client_var_list, client_h_list = [], []
            client_label_size_list = []
            client_dataset_size_list = []
            client_classifier_weight_keys = []
            sample_num_list = []
            for idx, device in enumerate(self._workers.keys()):
                (
                    client_var,
                    client_h,
                    client_label_size,
                    client_dataset_size,
                    client_cls_weight_keys,
                    sample_num,
                ) = self._workers[device].get_statistics()
                client_var_list.append(client_var.data)
                client_h_list.append(client_h)
                client_label_size_list.append(client_label_size)
                client_dataset_size_list.append(client_dataset_size)
                client_classifier_weight_keys.append(client_cls_weight_keys)
                sample_num_list.append(sample_num)

            # do local train
            client_param_list = []
            client_physical_device_type = None
            for step in range(0, train_steps_per_epoch, aggregate_freq):
                callbacks.on_train_batch_begin(batch=step)
                for idx, device in enumerate(self._workers.keys()):
                    # for distributing global model to clients
                    client_params = (
                        model_params_list[idx].to(device)
                        if model_params_list is not None
                        else None
                    )
                    # refresh data-iter
                    if step == 0:
                        self.kwargs["refresh_data"] = True
                    else:
                        self.kwargs["refresh_data"] = False

                    (
                        client_physical_device_type,
                        client_param,
                    ) = self._workers[device].train_step(
                        step,
                        epoch * train_steps_per_epoch + step,
                        (
                            aggregate_freq
                            if step + aggregate_freq < train_steps_per_epoch
                            else train_steps_per_epoch - step
                        ),
                        **self.kwargs,
                    )
                    if step == train_steps_per_epoch - 1:
                        # last step , save the model params
                        client_param_list.append(client_param)
                        res.append(client_params)

                # DP operation
                if dp_spent_step_freq is not None and self.dp_strategy is not None:
                    current_dp_step = math.ceil(
                        epoch * train_steps_per_epoch / aggregate_freq
                    ) + int(step / aggregate_freq)
                    if current_dp_step % dp_spent_step_freq == 0:
                        privacy_spent = self.dp_strategy.get_privacy_spent(
                            current_dp_step
                        )
                        logging.debug(f"DP privacy accountant {privacy_spent}")
                if len(res) == wait_steps:
                    wait(res)
                    res = []
                callbacks.on_train_batch_end(batch=step)

            # get every client's protos
            client_protos_list = []
            for idx, device in enumerate(self._workers.keys()):
                client_protos_list.append(
                    self._workers[device].get_local_protos_with_entire_dataset()
                )
            # last batch
            # update local infomation of every client
            if self._aggregator is not None:
                # fedpac
                # agg feature extraction
                model_params = self._aggregator.average(
                    data=client_param_list, axis=0, weights=sample_num_list
                )
                model_params_list = [model_params for _ in self.device_list]
                model_params_list = [
                    params.to(device)
                    for device, params in zip(self.device_list, model_params_list)
                ]
                # agg global protos
                global_protos = self._aggregator.global_protos_agg(
                    client_protos_list, client_label_size_list
                )
                # agg classifier
                cls_weight_list = self.classifier_collaboration_weight_compute(
                    client_physical_device_type.data,
                    client_var_list,
                    client_h_list,
                    **self.kwargs,
                )
                new_cls_list = {}
                for idx, device in enumerate(self._workers.keys()):
                    if cls_weight_list[idx] is not None:
                        new_cls = self._aggregator.classifier_weighted_aggregation(
                            client_param_list,
                            cls_weight_list[idx],
                            client_classifier_weight_keys[idx].data,
                            idx,
                        )
                    else:
                        new_cls = client_param_list[idx]
                    new_cls_list[device] = new_cls
                # apply weights
                for idx, device in enumerate(self._workers.keys()):
                    local_client = self._workers[device]
                    model_params = model_params_list[idx].data
                    new_cls = new_cls_list[device].data
                    local_client.apply_weights(
                        model_params,
                        global_protos,
                        new_cls,
                        **self.kwargs,
                    )
                    logging.info('apply_weights done')
            else:
                if self.server is not None:
                    # server will do aggregation
                    model_params_list = [
                        param.to(self.server) for param in client_param_list
                    ]
                    model_params_list = self.server(
                        self.server_agg_method,
                        num_returns=len(
                            self.device_list,
                        ),
                    )(model_params_list)
                    model_params_list = [
                        params.to(device)
                        for device, params in zip(self.device_list, model_params_list)
                    ]
                else:
                    raise Exception(
                        "Aggregation can be on either an aggregator or a server, but not none at the same time"
                    )

            local_metrics_obj = []
            for device, worker in self._workers.items():
                local_metrics_obj.append(worker.wrap_local_metrics())

            logging.info(f'local_metrics_obj: {local_metrics_obj}')
            if epoch % validation_freq == 0 and valid_x is not None:
                callbacks.on_test_begin()
                global_eval, local_eval = self.evaluate(
                    random_seed=random_seed,
                    return_dict=True,
                )
                for device, worker in self._workers.items():
                    worker.set_validation_metrics(global_eval)

                # save checkpoint
                if audit_log_dir is not None:
                    epoch_model_path = os.path.join(
                        audit_log_dir, "base_model", str(epoch)
                    )
                    self.save_model(
                        model_path=epoch_model_path, is_test=self.simulation
                    )
                callbacks.on_test_end()

            stop_trainings = [
                reveal(worker.get_stop_training()) for worker in self._workers.values()
            ]
            if sum(stop_trainings) >= self.consensus_num:
                break
            callbacks.on_epoch_end(epoch=epoch)
        callbacks.on_train_end()
        return callbacks.history

    def evaluate(self, random_seed, return_dict=False) -> Tuple[
        Union[List[Metric], Dict[str, Metric]],
        Union[Dict[str, List[Metric]], Dict[str, Dict[str, Metric]]],
    ]:
        local_metrics = {}
        metric_objs = {}
        for device, worker in self._workers.items():
            metric_objs[device.party] = worker.evaluate()
        local_metrics = reveal(metric_objs)
        logging.info(f"local_metrics: {local_metrics}")
        g_metrics = aggregate_metrics(local_metrics.values())
        if return_dict:
            return (
                {m.name: m for m in g_metrics},
                {
                    party: {m.name: m for m in metrics}
                    for party, metrics in local_metrics.items()
                },
            )
        else:
            return g_metrics, local_metrics
