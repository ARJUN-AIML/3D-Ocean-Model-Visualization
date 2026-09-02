"""
backend/api/schemas/observations.py
Pydantic Schemas for In-Situ Observation Metadata Discovery.
Reuses ObservationRecord models from backend.ml.schemas where appropriate.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ObservationSummary(BaseModel):
    """Metadata and spatial location of an observation platform/profile."""
    platform_id: str = Field(..., description="Unique platform ID (e.g. ARGO_2900001, GLIDER_SEA042)")
    instrument_type: str = Field(..., description="Sensor type: argo | glider | ctd | mooring | adcp")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    time: str = Field(..., description="Observation timestamp (ISO8601)")
    depth_min: Optional[float] = Field(None, description="Minimum depth measured in profile")
    depth_max: Optional[float] = Field(None, description="Maximum depth measured in profile")
    measurement_count: int = Field(..., description="Number of vertical profile measurements")


class ObservationDiscoveryResponse(BaseModel):
    """Response payload for observation discovery endpoint."""
    total_count: int = Field(..., description="Total count of matching observation profiles")
    observations: List[ObservationSummary] = Field(default_factory=list, description="List of observation profile summaries")
