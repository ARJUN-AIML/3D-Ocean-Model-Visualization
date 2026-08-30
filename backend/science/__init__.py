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
from .density import calculate_eos80_density, calculate_dataset_density, depth_to_pressure
from .slicing import OceanDataSlicer
from .dataset_manager import OceanDatasetManager
from .sample_generator import generate_indian_ocean_demo_dataset, DEMO_DATA_STATUS

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
    "calculate_eos80_density",
    "calculate_dataset_density",
    "depth_to_pressure",
    "OceanDataSlicer",
    "OceanDatasetManager",
    "generate_indian_ocean_demo_dataset",
    "DEMO_DATA_STATUS",
]
