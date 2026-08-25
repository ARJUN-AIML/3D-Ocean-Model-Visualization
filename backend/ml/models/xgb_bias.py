"""
backend/ml/models/xgb_bias.py
Generic XGBoost Ocean Model–Observation Bias Correction Model.
Predicts ocean state correction ΔV = V_obs - V_model for Temperature or Salinity
across Argo, Glider, CTD, Moorings, ADCP, and BGC sensors.
"""

from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
import xgboost as xgb

from backend.ml.schemas import BiasPredictionRequest, BiasPredictionResult
from backend.ml.preprocessing.normalization import TrainingFeatureScaler
from backend.ml.preprocessing.feature_engineering import FEATURE_COLUMNS, SENSOR_CODES


class XGBoostBiasCorrectionModel:
    """
    XGBoost Regressor for Ocean Numerical Model Bias Correction.
    Learns systematic physical biases between model predictions and in-situ observations.
    Sensor-agnostic and Target-variable-agnostic.
    """

    def __init__(
        self,
        model_version: str = "fusion_bias_correction_v1",
        target_variable: str = "temperature",
        sensor_type: str = "all",
        n_estimators: int = 100,
        max_depth: int = 5,
        learning_rate: float = 0.05,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        random_state: int = 42,
    ):
        self.model_version = model_version
        self.target_variable = target_variable
        self.sensor_type = sensor_type
        self.params = {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "learning_rate": learning_rate,
            "subsample": subsample,
            "colsample_bytree": colsample_bytree,
            "random_state": random_state,
            "n_jobs": -1,
        }
        self.model: Optional[xgb.XGBRegressor] = None
        self.scaler: Optional[TrainingFeatureScaler] = None
        self.is_trained: bool = False
        self.residual_std: float = 0.5  # default baseline residual std

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        scaler: Optional[TrainingFeatureScaler] = None,
    ) -> "XGBoostBiasCorrectionModel":
        """
        Trains the XGBoost Bias Correction model.

        Args:
            X_train: Unscaled training feature DataFrame.
            y_train: Target correction (obs_val - model_val).
            X_val: Unscaled validation feature DataFrame (optional).
            y_val: Validation target (optional).
            scaler: Optional pre-fitted scaler. If None, fits a new TrainingFeatureScaler on X_train.
        """
        if scaler is None:
            self.scaler = TrainingFeatureScaler()
            self.scaler.fit(X_train)
        else:
            self.scaler = scaler

        X_train_scaled = self.scaler.transform(X_train)

        self.model = xgb.XGBRegressor(**self.params)

        if X_val is not None and y_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            self.model.fit(
                X_train_scaled,
                y_train,
                eval_set=[(X_val_scaled, y_val)],
                verbose=False,
            )
            val_preds = self.model.predict(X_val_scaled)
            val_residuals = y_val - val_preds
            self.residual_std = float(np.std(val_residuals))
        else:
            self.model.fit(X_train_scaled, y_train, verbose=False)
            train_preds = self.model.predict(X_train_scaled)
            train_residuals = y_train - train_preds
            self.residual_std = float(np.std(train_residuals))

        self.is_trained = True
        return self

    def predict_df(self, df_features: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predicts target correction ΔV and corrected values for a DataFrame.

        Returns:
            (predicted_correction, corrected_values)
        """
        if not self.is_trained or self.model is None or self.scaler is None:
            raise RuntimeError("Model is not trained. Call train() before predicting.")

        X_scaled = self.scaler.transform(df_features[FEATURE_COLUMNS])
        predicted_corrections = self.model.predict(X_scaled)
        model_vals = df_features["model_value"].values
        corrected_vals = model_vals + predicted_corrections

        return predicted_corrections, corrected_vals

    def predict_single(self, request: BiasPredictionRequest) -> BiasPredictionResult:
        """
        Predicts bias correction for a single prediction request.
        """
        time_val = request.timestamp
        month = time_val.month
        day_of_year = time_val.timetuple().tm_yday

        # Select model_value based on target_variable
        if request.target_variable == "salinity":
            model_val = request.model_salinity if request.model_salinity is not None else 35.0
        else:
            model_val = request.model_temperature

        sensor_code = SENSOR_CODES.get(request.sensor_type.lower(), SENSOR_CODES["unknown"])

        single_dict = {
            "model_value": model_val,
            "model_temperature": request.model_temperature,
            "model_salinity": request.model_salinity if request.model_salinity is not None else 35.0,
            "model_u": request.model_u if request.model_u is not None else 0.0,
            "model_v": request.model_v if request.model_v is not None else 0.0,
            "depth": request.depth,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "spatial_distance_km": request.spatial_distance_km,
            "time_delta_hours": request.time_delta_hours,
            "depth_delta_m": request.depth_delta_m,
            "month": month,
            "day_of_year": day_of_year,
            "sin_month": np.sin(2.0 * np.pi * month / 12.0),
            "cos_month": np.cos(2.0 * np.pi * month / 12.0),
            "sensor_code": sensor_code,
        }

        df_single = pd.DataFrame([single_dict])
        corr, corrected = self.predict_df(df_single)

        return BiasPredictionResult(
            target_variable=request.target_variable,
            sensor_type=request.sensor_type,
            model_value=model_val,
            predicted_correction=float(corr[0]),
            corrected_value=float(corrected[0]),
            model_version=self.model_version,
            uncertainty_estimate=self.residual_std,
        )

    def get_feature_importances(self) -> Dict[str, float]:
        """Returns feature importance mapping."""
        if not self.is_trained or self.model is None:
            return {}
        importances = self.model.feature_importances_
        return {col: float(imp) for col, imp in zip(FEATURE_COLUMNS, importances)}
