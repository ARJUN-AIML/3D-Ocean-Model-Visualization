"""
backend/api/schemas/hycom.py
Pydantic Schemas for HYCOM Model Data Access.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class HycomVariableInfo(BaseModel):
    name: str = Field(..., description="Variable short name (e.g. TEMP, SALN, UVEL, VVEL, SSH, MLD, TCHP)")
    long_name: str = Field(..., description="Description long name")
    units: str = Field(..., description="Measurement units")
    dimensions: List[str] = Field(..., description="Variable dimensions")
    shape: List[int] = Field(..., description="Variable shape")


class HycomSummaryResponse(BaseModel):
    dataset_id: str = Field(..., description="HYCOM dataset identifier")
    source: str = Field("INCOIS RSMC HYCOM", description="Data source description")
    file_size_mb: float = Field(..., description="File size in megabytes")
    timesteps_count: int = Field(..., description="Total time steps")
    time_start: str = Field(..., description="Earliest ISO8601 timestamp")
    time_end: str = Field(..., description="Latest ISO8601 timestamp")
    depth_levels: List[float] = Field(..., description="Available depth levels in meters")
    lat_min: float = Field(..., description="Minimum latitude in degrees north")
    lat_max: float = Field(..., description="Maximum latitude in degrees north")
    lon_min: float = Field(..., description="Minimum longitude in degrees east")
    lon_max: float = Field(..., description="Maximum longitude in degrees east")
    variables: List[HycomVariableInfo] = Field(..., description="Available variables summary")


class HycomPointResponse(BaseModel):
    source: str = Field("INCOIS RSMC HYCOM", description="Data source name")
    variable: str = Field(..., description="Queried variable name")
    units: str = Field(..., description="Measurement units")
    requested_time: str = Field(..., description="User requested time")
    actual_time: str = Field(..., description="Matched dataset time (ISO8601)")
    requested_latitude: float = Field(..., description="User requested latitude")
    actual_latitude: float = Field(..., description="Matched grid latitude")
    requested_longitude: float = Field(..., description="User requested longitude")
    actual_longitude: float = Field(..., description="Matched grid longitude")
    requested_depth: float = Field(..., description="User requested depth in meters")
    actual_depth: float = Field(..., description="Matched grid depth in meters")
    value: Optional[float] = Field(..., description="Extracted numerical value or null if land/masked")


class HycomProfileResponse(BaseModel):
    source: str = Field("INCOIS RSMC HYCOM", description="Data source name")
    variable: str = Field(..., description="Queried variable name")
    units: str = Field(..., description="Measurement units")
    requested_time: str = Field(..., description="User requested time")
    actual_time: str = Field(..., description="Matched dataset time (ISO8601)")
    requested_latitude: float = Field(..., description="User requested latitude")
    actual_latitude: float = Field(..., description="Matched grid latitude")
    requested_longitude: float = Field(..., description="User requested longitude")
    actual_longitude: float = Field(..., description="Matched grid longitude")
    depths: List[float] = Field(..., description="Vertical depth levels in meters")
    values: List[Optional[float]] = Field(..., description="Extracted profile values at each depth level (null for land/masked)")
