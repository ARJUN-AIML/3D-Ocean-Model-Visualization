"""
backend/ml/tests/test_splitting.py
Unit tests for Chronological Splitting & Leakage Prevention.
"""

import pandas as pd
import pytest

from backend.ml.preprocessing.splitting import chronological_split, chronological_split_by_dates


def test_chronological_split_prevents_leakage():
    times = pd.date_range("2024-01-01", periods=100, freq="D")
    df = pd.DataFrame({
        "obs_time": times,
        "obs_temperature": [25.0] * 100,
        "model_temperature": [24.5] * 100,
    })

    df_train, df_val, df_test = chronological_split(
        df, time_col="obs_time", train_ratio=0.70, val_ratio=0.15, test_ratio=0.15
    )

    assert len(df_train) == 70
    assert len(df_val) == 15
    assert len(df_test) == 15

    # Strict Leakage check: max(train) < min(val) < min(test)
    assert df_train["obs_time"].max() < df_val["obs_time"].min()
    assert df_val["obs_time"].max() < df_test["obs_time"].min()


def test_chronological_split_by_dates():
    times = pd.date_range("2024-01-01", periods=30, freq="D")
    df = pd.DataFrame({
        "obs_time": times,
        "val": range(30),
    })

    df_train, df_val, df_test = chronological_split_by_dates(
        df, val_start_date="2024-01-20", test_start_date="2024-01-25", time_col="obs_time"
    )

    assert df_train["obs_time"].max() < pd.to_datetime("2024-01-20")
    assert df_val["obs_time"].min() >= pd.to_datetime("2024-01-20")
    assert df_val["obs_time"].max() < pd.to_datetime("2024-01-25")
    assert df_test["obs_time"].min() >= pd.to_datetime("2024-01-25")
