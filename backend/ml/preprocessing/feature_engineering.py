"""
backend/ml/preprocessing/feature_engineering.py
Sensor-Agnostic Feature Extraction and Target Construction Module.
Converts aligned model-observation DataFrames into ML-ready feature matrices X and targets y
for temperature or salinity bias correction across Argo, Glider, CTD, Moorings, ADCP, and BGC.
"""

from typing import List, Tuple, Dict, Any
import numpy as np
import pandas as pd

SENSOR_CODES: Dict[str, float] = {
    "argo": 0.0,
    "glider": 1.0,
    "ctd": 2.0,
    "mooring": 3.0,
    "adcp": 4.0,
    "bgc": 5.0,
    "satellite": 6.0,
    "unknown": 7.0,
}

FEATURE_COLUMNS = [
    "model_value",
    "model_temperature",
    "model_salinity",
    "model_u",
    "model_v",
    "depth",
    "latitude",
    "longitude",
    "spatial_distance_km",
    "time_delta_hours",
    "depth_delta_m",
    "month",
    "day_of_year",
    "sin_month",
    "cos_month",
    "sensor_code",
]

TARGET_COLUMN = "bias_target"


def extract_bias_correction_features(
    df: pd.DataFrame,
    target_variable: str = "temperature",
    is_training: bool = True
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Extracts features matrix X and target vector y from an aligned DataFrame.

    Target y = obs_target - model_target (the model error/bias).

    Args:
        df: Aligned model-observation DataFrame from ModelObservationAligner.
        target_variable: 'temperature' or 'salinity'.
        is_training: If True, computes and returns target y.

    Returns:
        (X, y)
    """
    df_feats = df.copy()

    # Target variable check
    obs_col = f"obs_{target_variable}"
    mod_col = f"model_{target_variable}"

    # Set model_value column dynamically
    if mod_col in df_feats.columns:
        df_feats["model_value"] = df_feats[mod_col]
    elif target_variable == "temperature" and "model_temperature" in df_feats.columns:
        df_feats["model_value"] = df_feats["model_temperature"]
    elif target_variable == "salinity" and "model_salinity" in df_feats.columns:
        df_feats["model_value"] = df_feats["model_salinity"]
    else:
        df_feats["model_value"] = 0.0

    # Rename lat/lon if needed
    if "obs_lat" in df_feats.columns:
        df_feats["latitude"] = df_feats["obs_lat"]
    if "obs_lon" in df_feats.columns:
        df_feats["longitude"] = df_feats["obs_lon"]

    # Spatial and temporal offset features
    for offset_col in ["spatial_distance_km", "time_delta_hours", "depth_delta_m"]:
        if offset_col not in df_feats.columns:
            df_feats[offset_col] = 0.0
        else:
            df_feats[offset_col] = df_feats[offset_col].fillna(0.0)

    # Sensor encoding
    if "instrument_type" in df_feats.columns:
        df_feats["sensor_code"] = df_feats["instrument_type"].str.lower().map(
            lambda s: SENSOR_CODES.get(str(s), SENSOR_CODES["unknown"])
        )
    else:
        df_feats["sensor_code"] = SENSOR_CODES["argo"]

    # Temporal feature engineering
    if "obs_time" in df_feats.columns:
        time_series = pd.to_datetime(df_feats["obs_time"])
        df_feats["month"] = time_series.dt.month
        df_feats["day_of_year"] = time_series.dt.dayofyear
    else:
        df_feats["month"] = 1
        df_feats["day_of_year"] = 1

    # Cyclical encoding for month
    df_feats["sin_month"] = np.sin(2.0 * np.pi * df_feats["month"] / 12.0)
    df_feats["cos_month"] = np.cos(2.0 * np.pi * df_feats["month"] / 12.0)

    # Impute missing velocity/salinity defaults safely if missing in model output
    if "model_temperature" not in df_feats.columns or df_feats["model_temperature"].isnull().all():
        df_feats["model_temperature"] = 25.0
    else:
        df_feats["model_temperature"] = df_feats["model_temperature"].fillna(25.0)

    if "model_salinity" not in df_feats.columns or df_feats["model_salinity"].isnull().all():
        df_feats["model_salinity"] = 35.0
    else:
        df_feats["model_salinity"] = df_feats["model_salinity"].fillna(35.0)

    if "model_u" not in df_feats.columns or df_feats["model_u"].isnull().all():
        df_feats["model_u"] = 0.0
    else:
        df_feats["model_u"] = df_feats["model_u"].fillna(0.0)

    if "model_v" not in df_feats.columns or df_feats["model_v"].isnull().all():
        df_feats["model_v"] = 0.0
    else:
        df_feats["model_v"] = df_feats["model_v"].fillna(0.0)

    X = df_feats[FEATURE_COLUMNS].copy()

    y = pd.Series(dtype=float)
    if is_training:
        if obs_col not in df_feats.columns or mod_col not in df_feats.columns:
            raise KeyError(f"Columns '{obs_col}' and '{mod_col}' are required to construct bias target.")
        y = df_feats[obs_col] - df_feats[mod_col]
        y.name = TARGET_COLUMN

    return X, y
