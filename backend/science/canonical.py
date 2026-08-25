"""
backend/science/canonical.py
Canonical Ocean Data Representation & Conventions.
Aligns with Section 8 of INCOIS 3D Ocean Data Visualization Platform Architecture Specification.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import xarray as xr

# Standard Variable Names (CF Convention compliant)
VAR_TEMPERATURE = "temperature"  # °C
VAR_SALINITY = "salinity"        # PSU
VAR_U_CURRENT = "u"              # m/s (eastward)
VAR_V_CURRENT = "v"              # m/s (northward)
VAR_W_CURRENT = "w"              # m/s (upward)
VAR_CHLOROPHYLL = "chlorophyll"  # mg/m³

# Canonical Coordinates
COORD_TIME = "time"
COORD_DEPTH = "depth"
COORD_LATITUDE = "latitude"
COORD_LONGITUDE = "longitude"

# Standard Mappings for heterogeneous input datasets
VARIABLE_ALIASES: Dict[str, str] = {
    "temp": VAR_TEMPERATURE,
    "t_an": VAR_TEMPERATURE,
    "votemper": VAR_TEMPERATURE,
    "thetao": VAR_TEMPERATURE,
    "sal": VAR_SALINITY,
    "s_an": VAR_SALINITY,
    "vosaline": VAR_SALINITY,
    "so": VAR_SALINITY,
    "u_current": VAR_U_CURRENT,
    "u_vel": VAR_U_CURRENT,
    "vozocrtx": VAR_U_CURRENT,
    "uo": VAR_U_CURRENT,
    "v_current": VAR_V_CURRENT,
    "v_vel": VAR_V_CURRENT,
    "vomecrty": VAR_V_CURRENT,
    "vo": VAR_V_CURRENT,
    "w_current": VAR_W_CURRENT,
    "w_vel": VAR_W_CURRENT,
    "vovecrtz": VAR_W_CURRENT,
    "wo": VAR_W_CURRENT,
    "chl": VAR_CHLOROPHYLL,
    "chlor_a": VAR_CHLOROPHYLL,
}

COORD_ALIASES: Dict[str, str] = {
    "lat": COORD_LATITUDE,
    "lats": COORD_LATITUDE,
    "nav_lat": COORD_LATITUDE,
    "latitude": COORD_LATITUDE,
    "lon": COORD_LONGITUDE,
    "long": COORD_LONGITUDE,
    "lons": COORD_LONGITUDE,
    "nav_lon": COORD_LONGITUDE,
    "longitude": COORD_LONGITUDE,
    "lev": COORD_DEPTH,
    "level": COORD_DEPTH,
    "depth_m": COORD_DEPTH,
    "z": COORD_DEPTH,
    "depth": COORD_DEPTH,
    "t": COORD_TIME,
    "datetime": COORD_TIME,
    "time": COORD_TIME,
}


def normalize_dataset_schema(ds: xr.Dataset) -> xr.Dataset:
    """
    Normalizes variable names, coordinate names, and depth conventions
    of an xarray.Dataset into canonical INCOIS representation.

    Rules:
    1. Rename coordinates and variables using standard alias maps.
    2. Ensure depth is positive-down (meters).
    3. Ensure longitude is in [-180, 180] or [0, 360] consistently (standardize to [-180, 180]).
    4. Preserve metadata, attributes, and handle missing values (NaN).
    """
    rename_map = {}

    # Identify coordinate renames
    for orig_name in list(ds.coords) + list(ds.dims):
        lower_name = str(orig_name).lower()
        if lower_name in COORD_ALIASES and COORD_ALIASES[lower_name] != orig_name:
            rename_map[orig_name] = COORD_ALIASES[lower_name]

    # Identify variable renames
    for orig_name in ds.data_vars:
        lower_name = str(orig_name).lower()
        if lower_name in VARIABLE_ALIASES and VARIABLE_ALIASES[lower_name] != orig_name:
            rename_map[orig_name] = VARIABLE_ALIASES[lower_name]

    if rename_map:
        ds = ds.rename(rename_map)

    # Standardize depth to positive-down
    if COORD_DEPTH in ds.coords:
        depth_vals = ds[COORD_DEPTH].values
        # If all depth values are negative, flip to positive
        if np.all(depth_vals <= 0) and not np.all(depth_vals == 0):
            ds = ds.assign_coords({COORD_DEPTH: np.abs(depth_vals)})
            ds[COORD_DEPTH].attrs["positive"] = "down"
            ds[COORD_DEPTH].attrs["units"] = "m"

    # Standardize longitude to [-180, 180] if max > 180
    if COORD_LONGITUDE in ds.coords:
        lon_vals = ds[COORD_LONGITUDE].values
        if np.any(lon_vals > 180):
            # Convert 0..360 to -180..180
            new_lons = ((lon_vals + 180) % 360) - 180
            # If coordinates are monotonic, re-index/sort
            ds = ds.assign_coords({COORD_LONGITUDE: new_lons})
            if ds.indexes.get(COORD_LONGITUDE) is not None:
                ds = ds.sortby(COORD_LONGITUDE)

    return ds


def validate_canonical_dataset(ds: xr.Dataset) -> Tuple[bool, List[str]]:
    """
    Validates whether an xarray Dataset adheres to canonical INCOIS requirements.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    required_coords = [COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE]
    for coord in required_coords:
        if coord not in ds.coords:
            errors.append(f"Missing required coordinate: {coord}")

    if not any(var in ds.data_vars for var in [VAR_TEMPERATURE, VAR_SALINITY, VAR_U_CURRENT, VAR_V_CURRENT]):
        errors.append("Dataset must contain at least one primary physical variable (temperature, salinity, u, v).")

    return len(errors) == 0, errors
