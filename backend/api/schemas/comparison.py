"""
backend/api/schemas/comparison.py
Pydantic Schemas for Model-Observation Comparison and Anomaly Services.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MatchMetadata(BaseModel):
    spatial_distance_km: float = Field(..., description="Distance between model grid cell and observation point in km")
    depth_diff_m: float = Field(..., description="Absolute depth difference in meters")
    time_diff_hours: float = Field(..., description="Absolute time difference in hours")
    interpolation_method: str = Field("trilinear_nearest", description="Interpolation/matching algorithm used")


class ComparisonPointResponse(BaseModel):
    platform_number: str = Field(..., description="Argo Float Platform WMO ID")
    cycle_number: int = Field(..., description="Float profile cycle index")
    time: str = Field(..., description="Observation timestamp (ISO8601)")
    latitude: float = Field(..., description="Observation latitude")
    longitude: float = Field(..., description="Observation longitude")
    depth: float = Field(..., description="Observation depth in meters")

    model_temperature: Optional[float] = Field(..., description="HYCOM predicted temperature (°C)")
    observed_temperature: Optional[float] = Field(..., description="Argo observed temperature (°C)")
    temperature_error: Optional[float] = Field(..., description="Temperature error (model - observed)")

    model_salinity: Optional[float] = Field(..., description="HYCOM predicted salinity (PSU)")
    observed_salinity: Optional[float] = Field(..., description="Argo observed salinity (PSU)")
    salinity_error: Optional[float] = Field(..., description="Salinity error (model - observed)")

    model_u: Optional[float] = Field(None, description="HYCOM predicted eastward current u (m/s)")
    model_v: Optional[float] = Field(None, description="HYCOM predicted northward current v (m/s)")

    matching_metadata: MatchMetadata = Field(..., description="Spatial-temporal matching metrics")


class AnomalyResponse(BaseModel):
    variable: str = Field(..., description="Analyzed variable (temperature or salinity)")
    units: str = Field(..., description="Physical units (°C or PSU)")
    time: str = Field(..., description="Timestamp of current observation/model value")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    depth: float = Field(..., description="Depth level in meters")

    current_value: Optional[float] = Field(..., description="Current observed/predicted value")
    baseline_mean: Optional[float] = Field(..., description="Historical 5-year VAM baseline mean value")
    baseline_std: Optional[float] = Field(None, description="Historical 5-year VAM baseline standard deviation")
    anomaly: Optional[float] = Field(..., description="Calculated anomaly (current_value - baseline_mean)")
    z_score: Optional[float] = Field(None, description="Calculated Z-score ((current_value - baseline_mean) / baseline_std)")
    source_baseline: str = Field("INCOIS Monthly Gridded Argo VAM", description="Baseline dataset name")
