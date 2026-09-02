"""
backend/api/schemas/ocean.py
Pydantic Schemas for Ocean Slicing and Variable Discovery.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class VariableSummary(BaseModel):
    """Metadata summary for a variable available in a dataset."""
    canonical_name: str = Field(..., description="Normalized CF-compliant variable name")
    original_name: str = Field(..., description="Original variable name in raw NetCDF file")
    units: str = Field(..., description="Measurement units (e.g. °C, PSU, m/s)")
    min_value: Optional[float] = Field(None, description="Minimum valid value")
    max_value: Optional[float] = Field(None, description="Maximum valid value")
    dimensions: List[str] = Field(..., description="Dimension names of variable")


class OceanSliceResponse(BaseModel):
    """
    Visualization-ready 2D Ocean Slice response payload.
    Contains explicit requested vs actual coordinates and JSON-safe values (NaN -> null).
    """
    dataset_id: str = Field(..., description="Dataset identifier")
    variable: str = Field(..., description="Canonical variable name")
    units: str = Field(..., description="Variable physical units")

    requested_time: str = Field(..., description="Time requested by user (ISO8601 or string)")
    actual_time: str = Field(..., description="Nearest matching time selected in dataset (ISO8601)")

    requested_depth: float = Field(..., description="Depth requested by user in meters")
    actual_depth: float = Field(..., description="Nearest matching depth selected in dataset in meters")

    latitude: List[float] = Field(..., description="Latitude grid coordinates")
    longitude: List[float] = Field(..., description="Longitude grid coordinates")

    # 2D Grid Array [len(lat), len(lon)]. Scientifically missing values (NaNs) are JSON null.
    values: List[List[Optional[float]]] = Field(..., description="2D slice array values (null for NaNs)")

    valid_min: Optional[float] = Field(None, description="Minimum non-null value in slice")
    valid_max: Optional[float] = Field(None, description="Maximum non-null value in slice")

    missing_value_count: int = Field(..., description="Total count of missing/NaN values in slice")

    source_metadata: Dict[str, Any] = Field(default_factory=dict, description="Dataset global attributes & spatial metadata")
