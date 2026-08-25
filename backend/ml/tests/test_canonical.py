"""
backend/ml/tests/test_canonical.py
Unit tests for Canonical Ocean Data Schema & Conventions.
"""

import numpy as np
import pytest
import xarray as xr

from backend.science.canonical import (
    normalize_dataset_schema,
    validate_canonical_dataset,
    COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE,
    VAR_TEMPERATURE, VAR_SALINITY
)


def test_normalize_dataset_schema_renames_aliases():
    # Create dataset with non-canonical alias names
    raw_ds = xr.Dataset(
        data_vars={
            "temp": (("t", "lev", "lat", "lon"), np.ones((2, 2, 2, 2))),
            "sal": (("t", "lev", "lat", "lon"), np.full((2, 2, 2, 2), 35.0)),
        },
        coords={
            "t": np.array(["2024-01-01", "2024-01-02"], dtype="datetime64[ns]"),
            "lev": np.array([-10.0, -50.0]),  # negative depths
            "lat": [10.0, 12.0],
            "lon": [70.0, 72.0],
        },
    )

    norm_ds = normalize_dataset_schema(raw_ds)

    assert VAR_TEMPERATURE in norm_ds.data_vars
    assert VAR_SALINITY in norm_ds.data_vars
    assert COORD_TIME in norm_ds.coords
    assert COORD_DEPTH in norm_ds.coords
    assert COORD_LATITUDE in norm_ds.coords
    assert COORD_LONGITUDE in norm_ds.coords

    # Verify depth positive-down normalization
    assert np.all(norm_ds[COORD_DEPTH].values >= 0)
    assert norm_ds[COORD_DEPTH].attrs.get("positive") == "down"


def test_validate_canonical_dataset(synthetic_ocean_model_ds):
    is_valid, errors = validate_canonical_dataset(synthetic_ocean_model_ds)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_invalid_dataset():
    invalid_ds = xr.Dataset(data_vars={"dummy": [1, 2, 3]})
    is_valid, errors = validate_canonical_dataset(invalid_ds)
    assert is_valid is False
    assert len(errors) > 0
