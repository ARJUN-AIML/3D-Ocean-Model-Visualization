"""
backend/ml/baselines/anomaly.py
Scientific Statistical Anomaly Baseline Module.
Implements climatological mean baseline, raw anomalies, and standardized z-score anomalies.
"""

from typing import Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd
import xarray as xr

from backend.science.canonical import COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE, VAR_TEMPERATURE


class StatisticalAnomalyBaseline:
    """
    Computes climatological baselines and statistical anomalies for ocean variables.
    Follows scientific standard:
        anomaly = value - climatology_mean
        standardized_anomaly = (value - climatology_mean) / climatology_std
    """

    def __init__(self, groupby_coord: str = "month"):
        """
        Args:
            groupby_coord: 'month' (1..12) or 'dayofyear' (1..366) to compute temporal climatology.
        """
        self.groupby_coord = groupby_coord
        self.climatology_mean: Optional[xr.DataArray] = None
        self.climatology_std: Optional[xr.DataArray] = None
        self.target_var: Optional[str] = None

    def fit(self, ds: xr.Dataset, variable: str = VAR_TEMPERATURE) -> "StatisticalAnomalyBaseline":
        """
        Fits climatological mean and standard deviation from a reference (training) dataset.
        """
        if variable not in ds.data_vars:
            raise KeyError(f"Variable '{variable}' not found in dataset.")

        self.target_var = variable
        da = ds[variable]

        # Extract temporal grouping coordinate
        if self.groupby_coord == "month":
            group_key = da[COORD_TIME].dt.month
        elif self.groupby_coord == "dayofyear":
            group_key = da[COORD_TIME].dt.dayofyear
        else:
            raise ValueError(f"Unsupported groupby_coord: {self.groupby_coord}")

        # Compute climatology mean and std across time dimension
        self.climatology_mean = da.groupby(group_key).mean(dim=COORD_TIME, skipna=True)
        self.climatology_std = da.groupby(group_key).std(dim=COORD_TIME, skipna=True)

        return self

    def compute_dataset_anomalies(self, ds: xr.Dataset, variable: Optional[str] = None) -> Tuple[xr.DataArray, xr.DataArray]:
        """
        Computes raw anomaly and standardized anomaly for a dataset using fitted climatology.

        Returns:
            (raw_anomaly, standardized_anomaly) as xarray DataArrays.
        """
        if self.climatology_mean is None or self.climatology_std is None:
            raise RuntimeError("Baseline must be fit on a training dataset before computing anomalies.")

        var_name = variable or self.target_var
        if var_name not in ds.data_vars:
            raise KeyError(f"Variable '{var_name}' not found in dataset.")

        da = ds[var_name]

        if self.groupby_coord == "month":
            group_key = da[COORD_TIME].dt.month
        else:
            group_key = da[COORD_TIME].dt.dayofyear

        # Subtract climatology mean for matching month/dayofyear
        raw_anomaly = da.groupby(group_key) - self.climatology_mean

        # Standardized anomaly (avoid division by 0 using small epsilon)
        std_safe = xr.where(self.climatology_std > 1e-6, self.climatology_std, np.nan)
        standardized_anomaly = raw_anomaly.groupby(group_key) / std_safe

        raw_anomaly.name = f"{var_name}_anomaly"
        standardized_anomaly.name = f"{var_name}_std_anomaly"

        return raw_anomaly, standardized_anomaly

    def compute_df_anomalies(
        self,
        df: pd.DataFrame,
        value_col: str,
        time_col: str = "time",
        depth_col: str = "depth",
    ) -> pd.DataFrame:
        """
        Computes statistical anomaly for a pandas DataFrame of point/profile observations.
        """
        df_out = df.copy()

        if not pd.api.types.is_datetime64_any_dtype(df_out[time_col]):
            df_out[time_col] = pd.to_datetime(df_out[time_col])

        if self.groupby_coord == "month":
            df_out["_group"] = df_out[time_col].dt.month
        else:
            df_out["_group"] = df_out[time_col].dt.dayofyear

        # Compute climatology by group and depth if not fit from dataset
        group_means = df_out.groupby(["_group", depth_col])[value_col].transform("mean")
        group_stds = df_out.groupby(["_group", depth_col])[value_col].transform("std")

        df_out[f"{value_col}_anomaly"] = df_out[value_col] - group_means
        std_safe = group_stds.replace(0, np.nan)
        df_out[f"{value_col}_std_anomaly"] = df_out[f"{value_col}_anomaly"] / std_safe

        df_out.drop(columns=["_group"], inplace=True)
        return df_out
