"""
backend/ml/tests/test_xgb_bias.py
Unit tests for Generic XGBoost Bias Correction Pipeline.
"""

from datetime import datetime
import numpy as np
import pandas as pd
import pytest

from backend.ml.models.xgb_bias import XGBoostBiasCorrectionModel
from backend.ml.schemas import BiasPredictionRequest
from backend.ml.preprocessing.feature_engineering import extract_bias_correction_features, FEATURE_COLUMNS


def test_xgb_bias_correction_train_predict():
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        "obs_temperature": np.random.uniform(15, 28, n) + 0.8,
        "model_temperature": np.random.uniform(15, 28, n),
        "model_salinity": np.full(n, 35.0),
        "model_u": np.full(n, 0.1),
        "model_v": np.full(n, -0.1),
        "depth": np.random.uniform(0, 200, n),
        "obs_lat": np.random.uniform(10, 15, n),
        "obs_lon": np.random.uniform(70, 75, n),
        "spatial_distance_km": np.random.uniform(0, 10, n),
        "time_delta_hours": np.random.uniform(0, 2, n),
        "depth_delta_m": np.random.uniform(0, 0.5, n),
        "instrument_type": ["argo"] * n,
        "obs_time": [datetime(2024, 1, 15)] * n,
    })

    X, y = extract_bias_correction_features(df, target_variable="temperature", is_training=True)

    model = XGBoostBiasCorrectionModel(n_estimators=20, max_depth=3)
    model.train(X, y)

    assert model.is_trained is True
    corr, corrected = model.predict_df(X)

    assert len(corr) == n
    assert len(corrected) == n
    assert np.allclose(corrected, X["model_value"].values + corr)

    importances = model.get_feature_importances()
    assert "model_value" in importances
    assert len(importances) == len(FEATURE_COLUMNS)


def test_predict_single_request():
    np.random.seed(42)
    df = pd.DataFrame({
        "obs_temperature": [25.8, 26.8, 27.8],
        "model_temperature": [25.0, 26.0, 27.0],
        "model_salinity": [35.0, 35.0, 35.0],
        "model_u": [0.0, 0.0, 0.0],
        "model_v": [0.0, 0.0, 0.0],
        "depth": [10.0, 20.0, 50.0],
        "obs_lat": [12.0, 12.5, 13.0],
        "obs_lon": [72.0, 72.5, 73.0],
        "spatial_distance_km": [0.5, 0.5, 0.5],
        "time_delta_hours": [0.1, 0.1, 0.1],
        "depth_delta_m": [0.0, 0.0, 0.0],
        "instrument_type": ["argo", "argo", "argo"],
        "obs_time": [datetime(2024, 1, 15)] * 3,
    })

    X, y = extract_bias_correction_features(df, target_variable="temperature", is_training=True)

    model = XGBoostBiasCorrectionModel(n_estimators=10, max_depth=2)
    model.train(X, y)

    req = BiasPredictionRequest(
        target_variable="temperature",
        sensor_type="argo",
        model_temperature=25.0,
        model_salinity=35.0,
        model_u=0.0,
        model_v=0.0,
        depth=10.0,
        latitude=12.0,
        longitude=72.0,
        timestamp=datetime(2024, 1, 15, 12, 0, 0),
        spatial_distance_km=0.5,
        time_delta_hours=0.1,
        depth_delta_m=0.0,
    )

    res = model.predict_single(req)

    assert res.model_value == 25.0
    assert abs(res.predicted_correction - 0.8) < 0.2
    assert res.corrected_value == res.model_value + res.predicted_correction
    assert res.uncertainty_estimate is not None
