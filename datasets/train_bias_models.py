"""
OceanTwin synthetic bias-correction training example.

IMPORTANT:
This trains on SYNTHETIC data only (Dataset 01: 01_matched_model_argo_training-2.csv).
Do not report the resulting metrics as real HYCOM/INCOIS scientific validation.

Target conventions:
  temp_error_obs_minus_model_c = obs_temp_c - model_temp_c
  sal_error_obs_minus_model_psu = obs_salinity_psu - model_salinity_psu

Corrected value:
  corrected_temp = model_temp_c + predicted_temp_error
  corrected_salinity = model_salinity_psu + predicted_salinity_error

Evaluated STRICTLY on held-out TEST split.
"""
from pathlib import Path
import sys
import json
import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from backend.science.dataset_loader import get_matched_training_data

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
BACKEND_MODEL_DIR = REPO_ROOT / "backend" / "ml" / "trained_models"
DATASETS_MODEL_DIR = ROOT / "trained_models"

BACKEND_MODEL_DIR.mkdir(parents=True, exist_ok=True)
DATASETS_MODEL_DIR.mkdir(parents=True, exist_ok=True)

df = get_matched_training_data()

# Keep only acceptable QC + reasonable matching gaps.
df = df[
    (df["temp_qc"].isin([1, 2])) &
    (df["sal_qc"].isin([1, 2])) &
    (df["distance_km"] <= 100) &
    (df["time_gap_hours"] <= 24)
].copy()

FEATURES = [
    "lat", "lon", "depth_m",
    "month_sin", "month_cos",
    "model_temp_c", "model_salinity_psu",
    "u_ms", "v_ms", "current_speed_ms"
]

def corr(y_true, y_pred):
    if len(y_true) < 2:
        return float("nan")
    return float(np.corrcoef(y_true, y_pred)[0, 1])

def compute_metrics(y_true, y_pred):
    err = y_pred - y_true
    return {
        "MAE": round(float(mean_absolute_error(y_true, y_pred)), 4),
        "RMSE": round(float(mean_squared_error(y_true, y_pred) ** 0.5), 4),
        "Bias_pred_minus_obs": round(float(np.mean(err)), 4),
        "R2": round(float(r2_score(y_true, y_pred)), 4),
        "Correlation": round(corr(y_true, y_pred), 4)
    }

def train_one(target_error_col, model_value_col, obs_col, out_name):
    train = df[df["split"] == "train"]
    val = df[df["split"] == "val"]
    test = df[df["split"] == "test"]

    model = XGBRegressor(
        n_estimators=700,
        learning_rate=0.035,
        max_depth=6,
        min_child_weight=3,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.03,
        reg_lambda=1.0,
        objective="reg:squarederror",
        random_state=26067,
        n_jobs=-1
    )

    model.fit(
        train[FEATURES],
        train[target_error_col],
        eval_set=[(val[FEATURES], val[target_error_col])],
        verbose=False
    )

    # Evaluate strictly on held-out TEST split
    predicted_error = model.predict(test[FEATURES])
    raw = test[model_value_col].to_numpy()
    corrected = raw + predicted_error
    obs = test[obs_col].to_numpy()

    result = {
        "raw_model": compute_metrics(obs, raw),
        "corrected_model": compute_metrics(obs, corrected),
        "n_train": int(len(train)),
        "n_val": int(len(val)),
        "n_test": int(len(test)),
        "features": FEATURES,
        "target": target_error_col,
        "dataset_type": "synthetic",
        "provenance": "OceanTwin Synthetic Demo Dataset (Dataset 01)"
    }

    for dir_path in [BACKEND_MODEL_DIR, DATASETS_MODEL_DIR]:
        joblib.dump(model, dir_path / f"{out_name}.joblib")
        with open(dir_path / f"{out_name}_metrics.json", "w") as f:
            json.dump(result, f, indent=2)

    print(f"\n=== {out_name} ===")
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    t_res = train_one(
        "temp_error_obs_minus_model_c",
        "model_temp_c",
        "obs_temp_c",
        "xgb_temperature_bias"
    )

    s_res = train_one(
        "sal_error_obs_minus_model_psu",
        "model_salinity_psu",
        "obs_salinity_psu",
        "xgb_salinity_bias"
    )

    print("\nSaved models and metrics to:", BACKEND_MODEL_DIR, "and", DATASETS_MODEL_DIR)

