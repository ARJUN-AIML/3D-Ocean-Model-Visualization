"""
backend/ml/schemas.py
Pydantic and Dataclass Data Schemas for Generic Model-Observation Fusion Engine.
Strict type contracts supporting Argo, Glider, CTD, Mooring, ADCP, BGC, and target variables (Temperature, Salinity).
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class SensorType(str, Enum):
    ARGO = "argo"
    GLIDER = "glider"
    CTD = "ctd"
    MOORING = "mooring"
    ADCP = "adcp"
    BGC = "bgc"
    SATELLITE = "satellite"
    UNKNOWN = "unknown"


class TargetVariable(str, Enum):
    TEMPERATURE = "temperature"
    SALINITY = "salinity"


class ProfileMeasurement(BaseModel):
    depth: float = Field(..., description="Depth in meters (positive down)")
    temperature: Optional[float] = Field(None, description="Observed temperature in °C")
    salinity: Optional[float] = Field(None, description="Observed salinity in PSU")
    chlorophyll: Optional[float] = Field(None, description="Observed chlorophyll in mg/m³")


class ObservationRecord(BaseModel):
    platform_id: str = Field(..., description="Platform identifier (e.g. Argo float or Glider ID)")
    instrument_type: str = Field(..., description="argo | glider | ctd | mooring | adcp | bgc")
    latitude: float = Field(..., description="WGS84 latitude in degrees (-90 to 90)")
    longitude: float = Field(..., description="WGS84 longitude in degrees (-180 to 180)")
    time: datetime = Field(..., description="Observation timestamp UTC")
    profiles: List[ProfileMeasurement] = Field(default_factory=list, description="Depth profile measurements")
    source_metadata: Dict[str, Any] = Field(default_factory=dict, description="Source provenance metadata")


class SpatialExtent(BaseModel):
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float


class TemporalRange(BaseModel):
    start_time: str
    end_time: str


class DepthRange(BaseModel):
    min_depth: float
    max_depth: float


class AlignedPoint(BaseModel):
    obs_platform_id: str
    instrument_type: str
    obs_time: datetime
    obs_lat: float
    obs_lon: float
    depth: float
    obs_temperature: Optional[float] = None
    obs_salinity: Optional[float] = None
    model_temperature: float
    model_salinity: Optional[float] = None
    model_u: Optional[float] = None
    model_v: Optional[float] = None
    spatial_distance_km: float
    time_delta_hours: float
    depth_delta_m: float
    interpolation_method: str = Field("nearest", description="nearest | trilinear")


class BiasPredictionRequest(BaseModel):
    target_variable: str = Field("temperature", description="temperature | salinity")
    sensor_type: str = Field("argo", description="argo | glider | ctd | mooring | adcp | bgc")
    model_temperature: float = Field(..., description="Uncorrected model temperature (°C)")
    model_salinity: Optional[float] = Field(35.0, description="Model salinity (PSU)")
    model_u: Optional[float] = Field(0.0, description="Model u-velocity (m/s)")
    model_v: Optional[float] = Field(0.0, description="Model v-velocity (m/s)")
    depth: float = Field(..., description="Depth in meters")
    latitude: float = Field(..., description="Latitude in degrees")
    longitude: float = Field(..., description="Longitude in degrees")
    timestamp: datetime = Field(..., description="Timestamp of prediction point")
    spatial_distance_km: float = Field(0.0, description="Spatial offset feature")
    time_delta_hours: float = Field(0.0, description="Temporal offset feature")
    depth_delta_m: float = Field(0.0, description="Depth offset feature")


class BiasPredictionResult(BaseModel):
    target_variable: str
    sensor_type: str
    model_value: float
    predicted_correction: float
    corrected_value: float
    baseline_error_mae: Optional[float] = None
    model_version: str
    uncertainty_estimate: Optional[float] = Field(None, description="Standard deviation/confidence interval of correction")


class MetricsSummary(BaseModel):
    target_variable: str = "temperature"
    baseline_mae: float
    baseline_rmse: float
    baseline_bias: float
    baseline_r2: float
    corrected_mae: float
    corrected_rmse: float
    corrected_bias: float
    corrected_r2: float
    mae_reduction_pct: float
    rmse_reduction_pct: float
    sample_count: int


class ModelMetadata(BaseModel):
    model_name: str = "xgb_fusion_bias_correction"
    model_version: str = "fusion_bias_correction_v1"
    sensor_type: str = "all"  # argo | glider | multi-sensor
    target_variable: str = "temperature"  # temperature | salinity
    training_dataset_hash: str
    features_used: List[str]
    spatial_extent: SpatialExtent
    temporal_range: TemporalRange
    training_period: TemporalRange
    validation_period: TemporalRange
    test_period: TemporalRange
    depth_range: DepthRange
    preprocessing_version: str = "v2.0"
    normalization_parameters: Dict[str, Dict[str, float]]
    evaluation_metrics: MetricsSummary
    trained_at: str
    git_commit: Optional[str] = "initial_dev"
