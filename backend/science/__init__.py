"""Backend science package initialization."""
from .canonical import (
    normalize_dataset_schema,
    validate_canonical_dataset,
    VAR_TEMPERATURE,
    VAR_SALINITY,
    VAR_U_CURRENT,
    VAR_V_CURRENT,
    VAR_W_CURRENT,
    VAR_CHLOROPHYLL,
    COORD_TIME,
    COORD_DEPTH,
    COORD_LATITUDE,
    COORD_LONGITUDE,
)

__all__ = [
    "normalize_dataset_schema",
    "validate_canonical_dataset",
    "VAR_TEMPERATURE",
    "VAR_SALINITY",
    "VAR_U_CURRENT",
    "VAR_V_CURRENT",
    "VAR_W_CURRENT",
    "VAR_CHLOROPHYLL",
    "COORD_TIME",
    "COORD_DEPTH",
    "COORD_LATITUDE",
    "COORD_LONGITUDE",
]
