"""
Unit tests for Chronological Data Leakage Prevention, Scaler Bounds, Held-out Evaluation, and Anomaly Severity.
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pytest

from backend.ml.preprocessing.splitting import chronological_split
from backend.ml.preprocessing.normalization import TrainingFeatureScaler
from backend.ml.baselines.anomaly import classify_anomaly_severity, StatisticalAnomalyBaseline
from backend.ml.evaluation.metrics import evaluate_bias_correction


def test_chronological_split_strict_ordering():
    """Validates that chronological split never mixes future timestamps into train set."""
    base_time = pd.Timestamp("2026-08-01")
    times = [base_time + pd.Timedelta(days=i) for i in range(100)]
    df = pd.DataFrame({
        "obs_time": times,
        "feature_1": np.random.randn(100),
        "obs_temperature": np.random.randn(100),
        "model_temperature": np.random.randn(100),
    })

    df_train, df_val, df_test = chronological_split(df, time_col="obs_time", train_ratio=0.70, val_ratio=0.15, test_ratio=0.15)

    assert len(df_train) == 70
    assert len(df_val) == 15
    assert len(df_test) == 15

    # Strict timestamp ordering assertion: max(train_time) <= min(val_time) <= max(val_time) <= min(test_time)
    assert df_train["obs_time"].max() <= df_val["obs_time"].min()
    assert df_val["obs_time"].max() <= df_test["obs_time"].min()


def test_scaler_fitted_strictly_on_train():
    """Validates data leakage prevention: scaler must fit strictly on train set features."""
    train_data = pd.DataFrame({"feat1": [1.0, 2.0, 3.0, 4.0, 5.0]})
    test_data = pd.DataFrame({"feat1": [10.0, 20.0, 30.0]})

    scaler = TrainingFeatureScaler()
    scaler.fit(train_data)

    mean_train = float(scaler.means["feat1"])
    assert mean_train == 3.0

    # Transform test set using train scaler without changing mean/std
    scaled_test = scaler.transform(test_data)
    assert scaler.means["feat1"] == 3.0  # Must not leak test set values into fitted means!


def test_anomaly_severity_classification():
    """Validates z-score anomaly severity tier boundaries."""
    assert classify_anomaly_severity(0.5) == "NORMAL"
    assert classify_anomaly_severity(-0.9) == "NORMAL"
    assert classify_anomaly_severity(1.5) == "WATCH"
    assert classify_anomaly_severity(-1.8) == "WATCH"
    assert classify_anomaly_severity(2.5) == "WARNING"
    assert classify_anomaly_severity(-2.9) == "WARNING"
    assert classify_anomaly_severity(3.5) == "CRITICAL"
    assert classify_anomaly_severity(-4.2) == "CRITICAL"


def test_evaluate_bias_correction_metrics():
    """Validates metrics calculation on held-out test data."""
    obs_vals = np.array([28.0, 29.0, 30.0, 27.0, 26.0])
    model_vals = np.array([27.0, 27.5, 28.5, 26.0, 25.0])  # Constant ~1.0°C cold bias
    corrected_vals = np.array([27.9, 28.9, 29.8, 26.9, 26.1])  # ML corrected close to obs

    metrics = evaluate_bias_correction(obs_vals, model_vals, corrected_vals, target_variable="temperature")

    assert metrics.baseline_mae > metrics.corrected_mae
    assert metrics.baseline_rmse > metrics.corrected_rmse
    assert metrics.mae_reduction_pct > 50.0  # > 50% improvement
