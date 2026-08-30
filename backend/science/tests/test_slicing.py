"""
Unit tests for Multidimensional Ocean Data Slicing Engine.
"""

import numpy as np
import pytest
import xarray as xr

from backend.science.slicing import OceanDataSlicer
from backend.science.canonical import (
    COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE,
    VAR_TEMPERATURE, VAR_SALINITY, VAR_U_CURRENT, VAR_V_CURRENT
)


@pytest.fixture
def sample_4d_dataset():
    """Creates synthetic 4D dataset for slicer testing."""
    times = ["2026-08-28T00:00:00", "2026-08-29T00:00:00"]
    depths = [0.0, 10.0, 100.0]
    lats = [10.0, 11.0, 12.0]
    lons = [60.0, 61.0, 62.0]

    temp_data = np.full((2, 3, 3, 3), 25.0)
    sal_data = np.full((2, 3, 3, 3), 35.0)
    u_data = np.full((2, 3, 3, 3), 0.5)
    v_data = np.full((2, 3, 3, 3), -0.3)

    # Insert a NaN to test NaN preservation
    temp_data[0, 0, 1, 1] = np.nan

    ds = xr.Dataset(
        data_vars={
            VAR_TEMPERATURE: (["time", "depth", "latitude", "longitude"], temp_data),
            VAR_SALINITY: (["time", "depth", "latitude", "longitude"], sal_data),
            VAR_U_CURRENT: (["time", "depth", "latitude", "longitude"], u_data),
            VAR_V_CURRENT: (["time", "depth", "latitude", "longitude"], v_data),
        },
        coords={
            COORD_TIME: times,
            COORD_DEPTH: depths,
            COORD_LATITUDE: lats,
            COORD_LONGITUDE: lons,
        },
    )
    return ds


def test_slicer_2d_slice(sample_4d_dataset):
    slicer = OceanDataSlicer(sample_4d_dataset)

    # Extract surface slice
    res = slicer.extract_2d_slice(VAR_TEMPERATURE, depth=0.0, time_index=0)
    assert res["variable"] == VAR_TEMPERATURE
    assert res["depth_actual"] == 0.0
    assert len(res["latitude"]) == 3
    assert len(res["longitude"]) == 3
    # Check NaN preservation
    assert res["data_grid"][1][1] is None
    assert res["data_grid"][0][0] == 25.0


def test_slicer_density_dynamic_calculation(sample_4d_dataset):
    slicer = OceanDataSlicer(sample_4d_dataset)
    res = slicer.extract_2d_slice("density", depth=10.0, time_index=0)

    assert res["variable"] == "density"
    assert res["min_val"] > 1000.0


def test_slicer_vertical_profile(sample_4d_dataset):
    slicer = OceanDataSlicer(sample_4d_dataset)
    prof = slicer.extract_vertical_profile(latitude=10.2, longitude=60.1, time_index=0)

    assert prof["actual_latitude"] == 10.0
    assert prof["actual_longitude"] == 60.0
    assert "temperature" in prof["profile"]
    assert len(prof["profile"]["depth"]) == 3


def test_slicer_velocity_vectors(sample_4d_dataset):
    slicer = OceanDataSlicer(sample_4d_dataset)
    vecs = slicer.extract_velocity_vectors(depth=0.0, time_index=0, stride=1)

    assert vecs["stride"] == 1
    assert "u" in vecs and "v" in vecs
    assert vecs["max_speed"] > 0.0
