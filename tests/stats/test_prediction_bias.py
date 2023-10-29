import math

import jax.numpy as jnp
import pandas as pd
import pytest

from secretflow import reveal
from secretflow.data import FedNdarray, PartitionWay
from secretflow.data import partition
from secretflow.data.vertical import VDataFrame
from secretflow.stats import prediction_bias_eval
from secretflow.stats.core.prediction_bias_core import PredictionBiasBucketMethod
from secretflow.stats.core.prediction_bias_core import prediction_bias as core

prediction = jnp.array([0.9, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 0.8])
label = jnp.array([1, 0, 0, 0, 0, 1, 1, 1])


@pytest.fixture(scope='module')
def prod_env_and_data(sf_production_setup_devices):
    y_actual_pd_dataframe = pd.DataFrame(
        {
            'y_actual': label,
        }
    )
    y_actual = VDataFrame(
        partitions={
            sf_production_setup_devices.alice: partition(
                data=sf_production_setup_devices.alice(lambda x: x)(
                    y_actual_pd_dataframe
                )
            ),
        }
    )

    y_prediction = FedNdarray(
        partitions={
            sf_production_setup_devices.alice: sf_production_setup_devices.alice(
                lambda x: x
            )(prediction.reshape((-1, 1)))
        },
        partition_way=PartitionWay.VERTICAL,
    )

    yield sf_production_setup_devices, {
        'y_actual': y_actual,
        "y_prediction": y_prediction,
    }


def test_eval(prod_env_and_data):
    env, data = prod_env_and_data
    report = reveal(
        prediction_bias_eval(
            data['y_prediction'], data['y_actual'], 4, True, 'equal_frequency'
        )
    )

    assert len(report.buckets) == 4

    assert math.isclose(report.buckets[0].avg_label, 0, rel_tol=1e-5)
    assert math.isclose(report.buckets[0].avg_prediction, 0.15, rel_tol=1e-5)
    assert math.isclose(report.buckets[0].left_endpoint, 0.1, rel_tol=1e-5)
    assert math.isclose(report.buckets[0].right_endpoint, 0.3, rel_tol=1e-5)
    assert math.isclose(report.buckets[0].bias, 0.15, rel_tol=1e-5)
    assert report.buckets[0].absolute
    assert report.buckets[0].left_closed
    assert not report.buckets[0].right_closed


def test_core():
    report = core(
        prediction=prediction,
        label=label,
        bucket_num=4,
        absolute=True,
        bucket_method=PredictionBiasBucketMethod.EQUAL_FREQUENCY,
        min_item_cnt_per_bucket=2,
    )
    assert len(report.buckets) == 4

    assert math.isclose(report.buckets[0].avg_label, 0, rel_tol=1e-5)
    assert math.isclose(report.buckets[0].avg_prediction, 0.15, rel_tol=1e-5)
    assert math.isclose(report.buckets[0].left_endpoint, 0.1, rel_tol=1e-5)
    assert math.isclose(report.buckets[0].right_endpoint, 0.3, rel_tol=1e-5)
    assert math.isclose(report.buckets[0].bias, 0.15, rel_tol=1e-5)
    assert report.buckets[0].absolute
    assert report.buckets[0].left_closed
    assert not report.buckets[0].right_closed

    assert math.isclose(report.buckets[1].avg_label, 0, rel_tol=1e-5)
    assert math.isclose(report.buckets[1].avg_prediction, 0.35, rel_tol=1e-5)
    assert math.isclose(report.buckets[1].left_endpoint, 0.3, rel_tol=1e-5)
    assert math.isclose(report.buckets[1].right_endpoint, 0.5, rel_tol=1e-5)
    assert math.isclose(report.buckets[1].bias, 0.35, rel_tol=1e-5)
    assert report.buckets[1].absolute
    assert report.buckets[1].left_closed
    assert not report.buckets[1].right_closed

    assert math.isclose(report.buckets[2].avg_label, 1, rel_tol=1e-5)
    assert math.isclose(report.buckets[2].avg_prediction, 0.6, rel_tol=1e-5)
    assert math.isclose(report.buckets[2].left_endpoint, 0.5, rel_tol=1e-5)
    assert math.isclose(report.buckets[2].right_endpoint, 0.8, rel_tol=1e-5)
    assert math.isclose(report.buckets[2].bias, 0.4, rel_tol=1e-5)
    assert report.buckets[2].absolute
    assert report.buckets[2].left_closed
    assert not report.buckets[2].right_closed

    assert math.isclose(report.buckets[3].avg_label, 1, rel_tol=1e-5)
    assert math.isclose(report.buckets[3].avg_prediction, 0.85, rel_tol=1e-5)
    assert math.isclose(report.buckets[3].left_endpoint, 0.8, rel_tol=1e-5)
    assert math.isclose(report.buckets[3].right_endpoint, 0.9, rel_tol=1e-5)
    assert math.isclose(report.buckets[3].bias, 0.15, rel_tol=1e-5)
    assert report.buckets[3].absolute
    assert report.buckets[3].left_closed
    assert report.buckets[3].right_closed

    report = core(
        prediction=prediction,
        label=label,
        bucket_num=4,
        absolute=False,
        bucket_method=PredictionBiasBucketMethod.EQUAL_WIDTH,
    )

    assert len(report.buckets) == 4

    assert math.isclose(report.buckets[0].avg_label, 0, rel_tol=1e-5)
    assert math.isclose(report.buckets[0].avg_prediction, 0.15, rel_tol=1e-5)
    assert math.isclose(report.buckets[0].left_endpoint, 0.1, rel_tol=1e-5)
    assert math.isclose(report.buckets[0].right_endpoint, 0.3, rel_tol=1e-5)
    assert math.isclose(report.buckets[0].bias, 0.15, rel_tol=1e-5)
    assert not report.buckets[0].absolute
    assert report.buckets[0].left_closed
    assert not report.buckets[0].right_closed

    assert math.isclose(report.buckets[1].avg_label, 0, rel_tol=1e-5)
    assert math.isclose(report.buckets[1].avg_prediction, 0.35, rel_tol=1e-5)
    assert math.isclose(report.buckets[1].left_endpoint, 0.3, rel_tol=1e-5)
    assert math.isclose(report.buckets[1].right_endpoint, 0.5, rel_tol=1e-5)
    assert math.isclose(report.buckets[1].bias, 0.35, rel_tol=1e-5)
    assert not report.buckets[1].absolute
    assert report.buckets[1].left_closed
    assert not report.buckets[1].right_closed

    assert math.isclose(report.buckets[2].avg_label, 1, rel_tol=1e-5)
    assert math.isclose(report.buckets[2].avg_prediction, 0.5, rel_tol=1e-5)
    assert math.isclose(report.buckets[2].left_endpoint, 0.5, rel_tol=1e-5)
    assert math.isclose(report.buckets[2].right_endpoint, 0.7, rel_tol=1e-5)
    assert math.isclose(report.buckets[2].bias, -0.5, rel_tol=1e-5)
    assert not report.buckets[2].absolute
    assert report.buckets[2].left_closed
    assert not report.buckets[2].right_closed

    assert math.isclose(report.buckets[3].avg_label, 1, rel_tol=1e-5)
    assert math.isclose(report.buckets[3].avg_prediction, 0.8, rel_tol=1e-5)
    assert math.isclose(report.buckets[3].left_endpoint, 0.7, rel_tol=1e-5)
    assert math.isclose(report.buckets[3].right_endpoint, 0.9, rel_tol=1e-5)
    assert math.isclose(report.buckets[3].bias, -0.2, rel_tol=1e-5)
    assert not report.buckets[3].absolute
    assert report.buckets[3].left_closed
    assert report.buckets[3].right_closed
