"""
backend/ml/service.py
High-Level Generic Model–Observation Fusion ML Service Layer.
Encapsulates end-to-end QC, ingestion, alignment, training, validation, test evaluation,
registry management, and inference for Argo, Glider, CTD, Moorings, ADCP, and BGC sensors.
"""

from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import xarray as xr

from backend.ml.schemas import (
    ObservationRecord,
    BiasPredictionRequest,
    BiasPredictionResult,
    MetricsSummary,
    ModelMetadata,
)
from backend.ml.baselines.anomaly import StatisticalAnomalyBaseline
from backend.ml.preprocessing.qc import QualityControlFilter
from backend.ml.preprocessing.alignment import ModelObservationAligner
from backend.ml.preprocessing.feature_engineering import extract_bias_correction_features
from backend.ml.preprocessing.splitting import chronological_split
from backend.ml.preprocessing.normalization import TrainingFeatureScaler
from backend.ml.models.xgb_bias import XGBoostBiasCorrectionModel
from backend.ml.evaluation.metrics import evaluate_bias_correction
from backend.ml.registry.metadata import ModelRegistry


class OceanMLService:
    """
    Unified Orchestrator Service for Ocean ML Tasks and Fusion Engine.
    """

    def __init__(self, registry_dir: str = "artifacts/ml_registry"):
        self.registry = ModelRegistry(registry_dir=registry_dir)
        self.qc_filter = QualityControlFilter()
        self.active_bias_model: Optional[XGBoostBiasCorrectionModel] = None
        self.anomaly_baseline = StatisticalAnomalyBaseline()

    def train_fusion_bias_pipeline(
        self,
        model_ds: xr.Dataset,
        observations: List[ObservationRecord],
        target_variable: str = "temperature",
        sensor_types: Optional[List[str]] = None,
        version_tag: Optional[str] = None,
        alignment_method: str = "nearest",
    ) -> Tuple[MetricsSummary, ModelMetadata]:
        """
        Runs generic end-to-end Fusion Model Bias Correction Pipeline.

        Pipeline Steps:
        1. Ingestion Quality Control filtering.
        2. Spatiotemporal alignment matching.
        3. Sensor-agnostic feature & target extraction (Target = obs_val - model_val).
        4. Chronological Train (70%) / Val (15%) / Test (15%) split.
        5. Scaler fitting strictly on Training set.
        6. XGBoost Model Training & Validation monitoring.
        7. Baseline vs. ML-Corrected evaluation on held-out Test set.
        8. Metadata artifact serialization to registry.
        """
        # Step 1: Quality Control
        clean_obs = self.qc_filter.filter_observations(observations)
        if not clean_obs:
            raise ValueError("No valid observation records passed Quality Control filtering.")

        # Determine sensor tag string
        if sensor_types is None:
            unique_sensors = sorted(list(set(o.instrument_type.lower() for s in [clean_obs] for o in s)))
            sensor_tag = "-".join(unique_sensors) if unique_sensors else "all"
        else:
            sensor_tag = "-".join(sorted([s.lower() for s in sensor_types]))

        auto_version = f"xgb_fusion_{sensor_tag}_{target_variable}_v1"
        final_version = version_tag or auto_version

        # Step 2: Alignment
        aligner = ModelObservationAligner(method=alignment_method)
        df_aligned = aligner.align_observations(
            model_ds=model_ds,
            observations=clean_obs,
            target_variable=target_variable,
            sensor_types=sensor_types,
        )

        if df_aligned.empty:
            raise ValueError(f"No aligned model-observation points found for target '{target_variable}' and sensors {sensor_types}.")

        # Step 3: Chronological Split
        df_train, df_val, df_test = chronological_split(
            df_aligned, time_col="obs_time", train_ratio=0.70, val_ratio=0.15, test_ratio=0.15
        )

        # Step 4: Feature Extraction
        X_train, y_train = extract_bias_correction_features(df_train, target_variable=target_variable, is_training=True)
        X_val, y_val = extract_bias_correction_features(df_val, target_variable=target_variable, is_training=True)
        X_test, y_test = extract_bias_correction_features(df_test, target_variable=target_variable, is_training=True)

        # Step 5: Scaler fit on Train set
        scaler = TrainingFeatureScaler()
        scaler.fit(X_train)

        # Step 6: Model Training
        bias_model = XGBoostBiasCorrectionModel(
            model_version=final_version,
            target_variable=target_variable,
            sensor_type=sensor_tag,
        )
        bias_model.train(X_train, y_train, X_val, y_val, scaler=scaler)

        # Step 7: Held-out Test Set Evaluation
        _, test_corrected_vals = bias_model.predict_df(X_test)
        target_obs_col = f"obs_{target_variable}"
        target_mod_col = f"model_{target_variable}"

        test_obs_vals = df_test[target_obs_col].values
        test_mod_vals = df_test[target_mod_col].values

        metrics = evaluate_bias_correction(
            obs_vals=test_obs_vals,
            model_vals=test_mod_vals,
            corrected_vals=test_corrected_vals,
            target_variable=target_variable,
        )

        # Step 8: Registry Saving
        self.registry.save_model(
            model=bias_model,
            df_train=df_train,
            df_val=df_val,
            df_test=df_test,
            metrics=metrics,
            sensor_type=sensor_tag,
            target_variable=target_variable,
            version=final_version,
        )

        self.active_bias_model = bias_model
        _, metadata = self.registry.load_model(final_version)
        return metrics, metadata

    def train_xgb_bias_pipeline(
        self,
        model_ds: xr.Dataset,
        observations: List[ObservationRecord],
        version_tag: str = "xgb_bias_correction_v1",
        alignment_method: str = "nearest",
    ) -> Tuple[MetricsSummary, ModelMetadata]:
        """Backward-compatibility wrapper for ML-01 pipeline."""
        return self.train_fusion_bias_pipeline(
            model_ds=model_ds,
            observations=observations,
            target_variable="temperature",
            sensor_types=None,
            version_tag=version_tag,
            alignment_method=alignment_method,
        )

    def load_bias_model(self, version_tag: str) -> ModelMetadata:
        """Loads trained bias model from registry into memory."""
        model, metadata = self.registry.load_model(version_tag)
        self.active_bias_model = model
        return metadata

    def predict_bias_correction(self, request: BiasPredictionRequest) -> BiasPredictionResult:
        """Executes single-point inference using active bias model."""
        if self.active_bias_model is None or not self.active_bias_model.is_trained:
            raise RuntimeError("No active trained bias model loaded. Call train_fusion_bias_pipeline or load_bias_model first.")
        return self.active_bias_model.predict_single(request)

    def fit_anomaly_baseline(self, ds: xr.Dataset, variable: str = "temperature") -> StatisticalAnomalyBaseline:
        """Fits statistical climatology anomaly baseline on dataset."""
        self.anomaly_baseline.fit(ds, variable=variable)
        return self.anomaly_baseline

    def compute_dataset_anomalies(self, ds: xr.Dataset, variable: str = "temperature") -> Tuple[xr.DataArray, xr.DataArray]:
        """Computes raw and standardized z-score anomalies for dataset."""
        return self.anomaly_baseline.compute_dataset_anomalies(ds, variable=variable)
