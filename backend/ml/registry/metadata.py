"""
backend/ml/registry/metadata.py
Model Registry and Metadata Manager for Model-Observation Fusion Engine.
Handles saving/loading of model weights, normalization scalers, and JSON metadata logs.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd

from backend.ml.schemas import ModelMetadata, MetricsSummary, SpatialExtent, TemporalRange, DepthRange
from backend.ml.models.xgb_bias import XGBoostBiasCorrectionModel
from backend.ml.preprocessing.normalization import TrainingFeatureScaler
from backend.ml.preprocessing.feature_engineering import FEATURE_COLUMNS


def compute_df_hash(df: pd.DataFrame) -> str:
    """Computes SHA-256 hash of training DataFrame for data traceability."""
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values).hexdigest()[:16]


def extract_temporal_range(df: pd.DataFrame, time_col: str = "obs_time") -> TemporalRange:
    """Extracts start_time and end_time strings from a DataFrame."""
    if not df.empty and time_col in df.columns:
        start_t = str(pd.to_datetime(df[time_col]).min())
        end_t = str(pd.to_datetime(df[time_col]).max())
    else:
        start_t, end_t = "N/A", "N/A"
    return TemporalRange(start_time=start_t, end_time=end_t)


class ModelRegistry:
    """
    Registry manager for model artifacts and metadata files.
    """

    def __init__(self, registry_dir: str = "artifacts/ml_registry"):
        self.registry_dir = registry_dir
        os.makedirs(self.registry_dir, exist_ok=True)

    def save_model(
        self,
        model: XGBoostBiasCorrectionModel,
        df_train: pd.DataFrame,
        df_val: pd.DataFrame,
        df_test: pd.DataFrame,
        metrics: MetricsSummary,
        sensor_type: str = "all",
        target_variable: str = "temperature",
        version: Optional[str] = None,
    ) -> str:
        """
        Saves XGBoost model, feature scaler, and metadata JSON artifact.

        Returns:
            model_version tag.
        """
        version_tag = version or model.model_version
        version_dir = os.path.join(self.registry_dir, version_tag)
        os.makedirs(version_dir, exist_ok=True)

        # Compute dataset extents
        all_df = pd.concat([df_train, df_val, df_test], ignore_index=True)
        min_lat = float(all_df["obs_lat"].min()) if "obs_lat" in all_df.columns else 0.0
        max_lat = float(all_df["obs_lat"].max()) if "obs_lat" in all_df.columns else 0.0
        min_lon = float(all_df["obs_lon"].min()) if "obs_lon" in all_df.columns else 0.0
        max_lon = float(all_df["obs_lon"].max()) if "obs_lon" in all_df.columns else 0.0
        min_depth = float(all_df["depth"].min()) if "depth" in all_df.columns else 0.0
        max_depth = float(all_df["depth"].max()) if "depth" in all_df.columns else 0.0

        overall_range = extract_temporal_range(all_df)
        train_range = extract_temporal_range(df_train)
        val_range = extract_temporal_range(df_val)
        test_range = extract_temporal_range(df_test)

        data_hash = compute_df_hash(all_df)
        scaler_dict = model.scaler.to_dict() if model.scaler else {}

        metadata = ModelMetadata(
            model_name="xgb_fusion_bias_correction",
            model_version=version_tag,
            sensor_type=sensor_type,
            target_variable=target_variable,
            training_dataset_hash=data_hash,
            features_used=FEATURE_COLUMNS,
            spatial_extent=SpatialExtent(
                min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon
            ),
            temporal_range=overall_range,
            training_period=train_range,
            validation_period=val_range,
            test_period=test_range,
            depth_range=DepthRange(min_depth=min_depth, max_depth=max_depth),
            preprocessing_version="v2.0",
            normalization_parameters=scaler_dict,
            evaluation_metrics=metrics,
            trained_at=datetime.now(timezone.utc).isoformat(),
            git_commit="ml02_fusion_dev",
        )

        # Save metadata json
        meta_path = os.path.join(version_dir, "metadata.json")
        with open(meta_path, "w") as f:
            f.write(metadata.model_dump_json(indent=2))

        # Save XGBoost binary model
        if model.model is not None:
            xgb_path = os.path.join(version_dir, "model.json")
            model.model.save_model(xgb_path)

        return version_tag

    def load_model(self, version_tag: str) -> Tuple[XGBoostBiasCorrectionModel, ModelMetadata]:
        """
        Loads XGBoost model and associated metadata from registry.
        """
        version_dir = os.path.join(self.registry_dir, version_tag)
        meta_path = os.path.join(version_dir, "metadata.json")
        xgb_path = os.path.join(version_dir, "model.json")

        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"Metadata file not found for version {version_tag} at {meta_path}")

        with open(meta_path, "r") as f:
            metadata_dict = json.load(f)
        metadata = ModelMetadata(**metadata_dict)

        scaler = TrainingFeatureScaler.from_dict(metadata.normalization_parameters)

        model_instance = XGBoostBiasCorrectionModel(
            model_version=version_tag,
            target_variable=metadata.target_variable,
            sensor_type=metadata.sensor_type,
        )
        model_instance.scaler = scaler

        if os.path.exists(xgb_path):
            import xgboost as xgb
            model_instance.model = xgb.XGBRegressor()
            model_instance.model.load_model(xgb_path)
            model_instance.is_trained = True

        return model_instance, metadata
