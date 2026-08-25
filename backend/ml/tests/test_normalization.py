"""
backend/ml/tests/test_normalization.py
Unit tests for Training-Only Feature Normalization.
"""

import numpy as np
import pandas as pd
import pytest

from backend.ml.preprocessing.normalization import TrainingFeatureScaler


def test_training_feature_scaler_fit_transform():
    df_train = pd.DataFrame({
        "feat_a": [10.0, 20.0, 30.0, 40.0, 50.0],
        "feat_b": [1.0, 2.0, 3.0, 4.0, 5.0],
    })

    scaler = TrainingFeatureScaler()
    scaler.fit(df_train)

    assert scaler.is_fitted is True
    assert abs(scaler.means["feat_a"] - 30.0) < 1e-5

    scaled_train = scaler.transform(df_train)
    # Mean of scaled training data should be ~0
    assert abs(scaled_train["feat_a"].mean()) < 1e-5

    # Test transform on unseen val set using train parameters
    df_val = pd.DataFrame({
        "feat_a": [60.0, 70.0],
        "feat_b": [6.0, 7.0],
    })
    scaled_val = scaler.transform(df_val)
    # Val values transformed using train mean=30 and train std=15.811
    expected_val_a_0 = (60.0 - 30.0) / scaler.stds["feat_a"]
    assert abs(scaled_val["feat_a"].iloc[0] - expected_val_a_0) < 1e-5


def test_scaler_dict_roundtrip():
    df_train = pd.DataFrame({
        "feat_a": [10.0, 20.0, 30.0],
    })
    scaler = TrainingFeatureScaler()
    scaler.fit(df_train)

    param_dict = scaler.to_dict()
    scaler_reconstructed = TrainingFeatureScaler.from_dict(param_dict)

    assert scaler_reconstructed.is_fitted is True
    assert scaler_reconstructed.means["feat_a"] == scaler.means["feat_a"]
    assert scaler_reconstructed.stds["feat_a"] == scaler.stds["feat_a"]
