"""
backend/ml/tests/test_anomaly.py
Unit tests for Statistical Anomaly Baseline.
"""

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from backend.ml.baselines.anomaly import StatisticalAnomalyBaseline
from backend.science.canonical import VAR_TEMPERATURE, COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE


def test_statistical_anomaly_baseline_fit_and_compute(synthetic_ocean_model_ds):
    baseline = StatisticalAnomalyBaseline(groupby_coord="month")
    baseline.fit(synthetic_ocean_model_ds, variable=VAR_TEMPERATURE)

    assert baseline.climatology_mean is not None
    assert baseline.climatology_std is not None

    raw_anom, std_anom = baseline.compute_dataset_anomalies(synthetic_ocean_model_ds)

    assert raw_anom.name == f"{VAR_TEMPERATURE}_anomaly"
    assert std_anom.name == f"{VAR_TEMPERATURE}_std_anomaly"
    assert raw_anom.shape == synthetic_ocean_model_ds[VAR_TEMPERATURE].shape

    # Mean of raw anomalies over time should be near 0
    anom_mean = float(raw_anom.mean().values)
    assert abs(anom_mean) < 1e-4


def test_df_anomaly_computation():
    baseline = StatisticalAnomalyBaseline(groupby_coord="month")
    df_obs = pd.DataFrame({
        "time": pd.date_range("2024-01-01", periods=10, freq="D"),
        "depth": [10.0] * 10,
        "temperature": [25.0, 26.0, 25.5, 24.5, 25.0, 27.0, 26.5, 25.0, 25.5, 26.0],
    })

    df_anom = baseline.compute_df_anomalies(df_obs, value_col="temperature")

    assert "temperature_anomaly" in df_anom.columns
    assert "temperature_std_anomaly" in df_anom.columns
    assert not df_anom["temperature_anomaly"].isnull().all()
