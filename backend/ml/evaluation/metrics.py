"""
backend/ml/evaluation/metrics.py
Evaluation Metrics Module comparing Ocean Model Baseline vs ML-Corrected Model.
Reports MAE, RMSE, Mean Bias, R², and relative error reduction for Temperature and Salinity.
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from backend.ml.schemas import MetricsSummary


def compute_error_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Computes MAE, RMSE, Mean Bias, and R² for target and predictions.
    """
    mask = ~np.isnan(y_true) & ~np.isnan(y_pred)
    if not np.any(mask):
        return {"mae": np.nan, "rmse": np.nan, "bias": np.nan, "r2": np.nan}

    yt = y_true[mask]
    yp = y_pred[mask]

    mae = float(mean_absolute_error(yt, yp))
    rmse = float(np.sqrt(mean_squared_error(yt, yp)))
    bias = float(np.mean(yp - yt))

    if len(np.unique(yt)) <= 1:
        r2 = 1.0 if np.allclose(yt, yp) else 0.0
    else:
        r2 = float(r2_score(yt, yp))

    return {
        "mae": mae,
        "rmse": rmse,
        "bias": bias,
        "r2": r2,
    }


def evaluate_bias_correction(
    obs_vals: np.ndarray,
    model_vals: np.ndarray,
    corrected_vals: np.ndarray,
    target_variable: str = "temperature",
) -> MetricsSummary:
    """
    Compares Baseline Ocean Model (model_vals vs obs_vals)
    against ML-Corrected Model (corrected_vals vs obs_vals).

    Returns:
        MetricsSummary containing baseline vs corrected metrics and error reduction %.
    """
    baseline_metrics = compute_error_metrics(obs_vals, model_vals)
    corrected_metrics = compute_error_metrics(obs_vals, corrected_vals)

    b_mae = baseline_metrics["mae"]
    c_mae = corrected_metrics["mae"]
    mae_red = float(((b_mae - c_mae) / b_mae) * 100.0) if b_mae > 1e-6 else 0.0

    b_rmse = baseline_metrics["rmse"]
    c_rmse = corrected_metrics["rmse"]
    rmse_red = float(((b_rmse - c_rmse) / b_rmse) * 100.0) if b_rmse > 1e-6 else 0.0

    valid_samples = int(np.sum(~np.isnan(obs_vals) & ~np.isnan(model_vals) & ~np.isnan(corrected_vals)))

    return MetricsSummary(
        target_variable=target_variable,
        baseline_mae=b_mae,
        baseline_rmse=b_rmse,
        baseline_bias=baseline_metrics["bias"],
        baseline_r2=baseline_metrics["r2"],
        corrected_mae=c_mae,
        corrected_rmse=c_rmse,
        corrected_bias=corrected_metrics["bias"],
        corrected_r2=corrected_metrics["r2"],
        mae_reduction_pct=mae_red,
        rmse_reduction_pct=rmse_red,
        sample_count=valid_samples,
    )
