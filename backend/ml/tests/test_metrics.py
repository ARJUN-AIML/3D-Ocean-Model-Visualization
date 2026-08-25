"""
backend/ml/tests/test_metrics.py
Unit tests for Evaluation Metrics and Baseline Comparison.
"""

import numpy as np
import pytest

from backend.ml.evaluation.metrics import compute_error_metrics, evaluate_bias_correction


def test_compute_error_metrics():
    y_true = np.array([25.0, 26.0, 27.0, 28.0])
    y_pred = np.array([25.5, 25.5, 27.5, 27.5])

    metrics = compute_error_metrics(y_true, y_pred)

    assert metrics["mae"] == 0.5
    assert abs(metrics["rmse"] - 0.5) < 1e-4
    assert metrics["bias"] == 0.0  # (0.5 - 0.5 + 0.5 - 0.5) / 4 = 0


def test_evaluate_bias_correction_improvement():
    obs_temp = np.array([26.0, 27.0, 28.0, 29.0])
    # Baseline model underpredicts systematically by 1.0°C
    model_temp = np.array([25.0, 26.0, 27.0, 28.0])
    # ML corrected model removes systematic bias
    corrected_temp = np.array([25.9, 27.1, 27.95, 29.05])

    summary = evaluate_bias_correction(obs_temp, model_temp, corrected_temp)

    assert summary.baseline_mae == 1.0
    assert summary.corrected_mae < 0.1
    assert summary.mae_reduction_pct > 90.0
    assert summary.rmse_reduction_pct > 90.0
    assert summary.sample_count == 4
