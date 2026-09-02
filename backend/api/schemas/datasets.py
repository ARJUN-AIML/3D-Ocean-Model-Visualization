"""
backend/api/schemas/datasets.py
Pydantic Schemas for Dataset Discovery and Metadata.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service operational status")
    service_name: str = Field(..., description="Service name")
    version: str = Field(..., description="API Version")


class DatasetSummary(BaseModel):
    """Summary representation of a discovered dataset."""
    dataset_id: str = Field(..., description="Unique dataset identifier / relative filename")
    display_name: str = Field(..., description="Human readable dataset title")
    source_type: str = Field(..., description="Type of source data (e.g. 'model', 'observation')")
    format: str = Field(..., description="File format (e.g. 'NetCDF-4/HDF5', 'CSV')")
    available_variables: List[str] = Field(default_factory=list, description="Canonical variable names present")
    time_range: Optional[List[str]] = Field(None, description="ISO8601 time bounds [min_time, max_time]")
    depth_range: Optional[List[float]] = Field(None, description="Depth bounds in meters [min_depth, max_depth]")
    latitude_range: Optional[List[float]] = Field(None, description="Latitude bounds [min_lat, max_lat]")
    longitude_range: Optional[List[float]] = Field(None, description="Longitude bounds [min_lon, max_lon]")


class CoordinateInfo(BaseModel):
    """Detailed metadata for a coordinate dimension."""
    dtype: str
    range: List[Any]
    units: str
    size: int


class VariableInfo(BaseModel):
    """Detailed metadata for a data variable."""
    dtype: str
    range: List[Any]
    units: str
    missing_pct: float
    chunking: str
    compression: str


class BoundingBox(BaseModel):
    """Geographic spatial coverage."""
    latitude_range: List[float]
    longitude_range: List[float]


class TimeRange(BaseModel):
    """Temporal coverage information."""
    start_time: str
    end_time: str
    timesteps_count: int


class DepthRange(BaseModel):
    """Vertical depth coverage information."""
    min_depth: float
    max_depth: float
    levels_count: int


class DatasetDetail(DatasetSummary):
    """Detailed dataset metadata profile."""
    file_size_mb: float
    dimensions: Dict[str, int]
    coordinates: Dict[str, CoordinateInfo]
    variables: Dict[str, VariableInfo]
    spatial_coverage: BoundingBox
    temporal_coverage: Optional[TimeRange] = None
    depth_coverage: Optional[DepthRange] = None
    visualization_capabilities: Dict[str, bool]
    scientific_issues: List[Dict[str, Any]] = Field(default_factory=list)
