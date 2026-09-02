"""
backend/api/schemas/baseline.py
Pydantic Schemas for Monthly Gridded Argo VAM Baseline Data Access.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class BaselineSummaryResponse(BaseModel):
    dataset_id: str = Field("incois_argo_mnt_VAM.nc", description="VAM Baseline dataset identifier")
    source: str = Field("INCOIS Monthly Gridded Argo VAM", description="Data source description")
    file_size_mb: float = Field(..., description="File size in megabytes")
    timesteps_count: int = Field(61, description="Total monthly time steps (2020-2025)")
    time_start: str = Field(..., description="Earliest ISO8601 timestamp")
    time_end: str = Field(..., description="Latest ISO8601 timestamp")
    depth_levels: List[float] = Field(..., description="24 vertical depth levels in meters")
    lat_min: float = Field(-29.5, description="Minimum latitude")
    lat_max: float = Field(29.5, description="Maximum latitude")
    lon_min: float = Field(30.5, description="Minimum longitude")
    lon_max: float = Field(119.5, description="Maximum longitude")
    grid_resolution_deg: float = Field(1.0, description="Horizontal grid resolution in degrees")


class BaselinePointResponse(BaseModel):
    source: str = Field("INCOIS Monthly Gridded Argo VAM", description="Data source name")
    variable: str = Field(..., description="Queried baseline variable (TEMP or SAL)")
    units: str = Field(..., description="Physical measurement units (°C or PSU)")
    month: int = Field(..., description="Target month of year (1-12)")
    matched_time: str = Field(..., description="Matched climatological timestamp")
    requested_latitude: float = Field(..., description="User requested latitude")
    actual_latitude: float = Field(..., description="Matched grid latitude")
    requested_longitude: float = Field(..., description="User requested longitude")
    actual_longitude: float = Field(..., description="Matched grid longitude")
    requested_depth: float = Field(..., description="User requested depth in meters")
    actual_depth: float = Field(..., description="Matched grid depth in meters")
    baseline_mean: Optional[float] = Field(..., description="5-year monthly climatological mean value")
    baseline_std: Optional[float] = Field(None, description="Monthly standard deviation across 5 years if available")


class BaselineProfileResponse(BaseModel):
    source: str = Field("INCOIS Monthly Gridded Argo VAM", description="Data source name")
    variable: str = Field(..., description="Queried baseline variable (TEMP or SAL)")
    units: str = Field(..., description="Physical measurement units")
    month: int = Field(..., description="Target month of year (1-12)")
    matched_time: str = Field(..., description="Matched climatological timestamp")
    requested_latitude: float = Field(..., description="User requested latitude")
    actual_latitude: float = Field(..., description="Matched grid latitude")
    requested_longitude: float = Field(..., description="User requested longitude")
    actual_longitude: float = Field(..., description="Matched grid longitude")
    depths: List[float] = Field(..., description="24 vertical depth levels in meters")
    baseline_means: List[Optional[float]] = Field(..., description="Profile mean values at each depth level")
    baseline_stds: List[Optional[float]] = Field(default_factory=list, description="Profile standard deviation values at each depth level")
