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

from typing import Union, Callable, Dict
from functools import partial

import numpy as np
import pandas as pd
from sklearn.preprocessing import FunctionTransformer as SkFunctionTransformer

from secretflow.data.base import Partition
from secretflow.data.horizontal import HDataFrame
from secretflow.data.mix import MixDataFrame
from secretflow.data.vertical import VDataFrame


def _check_dataframe(df):
    assert isinstance(
        df, (HDataFrame, VDataFrame, MixDataFrame)
    ), f'Accepts HDataFrame/VDataFrame/MixDataFrame only but got {type(df)}'


class _FunctionTransformer:
    """Constructs a transformer from an arbitrary callable.

    Just same as :py:class:`sklearn.preprocessing.FunctionTransformer`
    where the input/ouput is federated dataframe.

    Args:
        func: callable, default=None
            The callable to use for the transformation.
            If func is None, then func will be the identity function.
            Lambda is not supported here.

        kw_args: dict, default=None
            Dictionary of additional keyword arguments to pass to func.

    Attributes:
        _transformer: the sklearn FunctionTransformer instance.

    Examples:
        >>> from secretflow.preprocessing import _FunctionTransformer
        >>> ft = _FunctionTransformer(np.log1p)
        >>> ft.fit(df)
        >>> ft.transform(df)
    """

    def __init__(self, func: Callable, kw_args: Dict = None):
        self._transformer = SkFunctionTransformer(func=func, kw_args=kw_args)

    def _fit(self, df: Union[HDataFrame, VDataFrame]) -> np.ndarray:
        def _df_fit(df: pd.DataFrame):
            self._transformer.fit(df)

        for device, part in df.partitions.items():
            device(_df_fit)(part.data)

    def fit(self, df: Union[HDataFrame, VDataFrame, MixDataFrame]):
        """Fit label encoder."""
        _check_dataframe(df)

        if isinstance(df, (HDataFrame, VDataFrame)):
            self._fit(df)
        else:
            for part in df.partitions:
                self._fit(part)

    def _transform(
        self, df: Union[HDataFrame, VDataFrame]
    ) -> Union[HDataFrame, VDataFrame]:
        def _df_transform(transformer: SkFunctionTransformer, df: pd.DataFrame):
            return pd.DataFrame(
                data=transformer.transform(df),
                columns=df.columns,
            )

        transformed_parts = {}
        for device, part in df.partitions.items():
            transformed_parts[device] = Partition(
                device(_df_transform)(self._transformer, part.data)
            )

        new_df = df.copy()
        new_df.partitions = transformed_parts
        return new_df

    def transform(
        self, df: Union[HDataFrame, VDataFrame, MixDataFrame]
    ) -> Union[HDataFrame, VDataFrame, MixDataFrame]:
        """Transform labels with function."""
        _check_dataframe(df)

        if isinstance(df, (HDataFrame, VDataFrame)):
            return self._transform(df)
        else:
            return MixDataFrame(
                partitions=[self._transform(part) for part in df.partitions]
            )

    def fit_transform(
        self, df: Union[HDataFrame, VDataFrame]
    ) -> Union[HDataFrame, VDataFrame, MixDataFrame]:
        """Fit function transformer and return transformed DataFrame."""
        self.fit(df)
        return self.transform(df)


class LogroundTransformer(_FunctionTransformer):
    """Constructs a transformer for calculating round(log2(x + bias)) of (partition of) dataframe.

    Args:
        decimals: Number of decimal places to round each column to. Defaults to 6.
        bias: Add bias to value before log2. Defaults to 0.5.

    """

    def __init__(self, decimals: int = 6, bias: float = 0.5):
        def _loground(
            x: pd.DataFrame, decimals: int = 6, bias: float = 0.5
        ) -> pd.DataFrame:
            return x.add(bias).apply(np.log2).round(decimals=decimals)

        super().__init__(partial(_loground, decimals=decimals, bias=bias))
