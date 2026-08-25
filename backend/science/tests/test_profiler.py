"""
backend/science/tests/test_profiler.py
Unit tests for Scientific Dataset Validator and Dataset Profiler.
"""

import os
import numpy as np
import pandas as pd
import pytest
import xarray as xr

from backend.science.validator import OceanDatasetValidator
from backend.science.profiler import DatasetProfiler, generate_validation_reports
from backend.science.canonical import VAR_TEMPERATURE, VAR_SALINITY, COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE


def test_validator_detects_unphysical_values():
    validator = OceanDatasetValidator()
    ds = xr.Dataset(
        data_vars={
            VAR_TEMPERATURE: ((COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE), np.full((2, 2, 2, 2), 99.0)), # unphysical 99°C
        },
        coords={
            COORD_TIME: pd.date_range("2024-01-01", periods=2),
            COORD_DEPTH: [10.0, 20.0],
            COORD_LATITUDE: [10.0, 95.0], # invalid lat 95°
            COORD_LONGITUDE: [70.0, 72.0],
        },
    )

    issues = validator.validate_dataset(ds, filename="unphysical_test.nc")

    issue_types = [i.issue_type for i in issues]
    assert "LATITUDE_OUT_OF_BOUNDS" in issue_types
    assert "UNPHYSICAL_TEMPERATURE_VALUE" in issue_types


def test_validator_detects_non_monotonic_time():
    validator = OceanDatasetValidator()
    # Out of order timestamps
    times = pd.to_datetime(["2024-01-05", "2024-01-01"])
    ds = xr.Dataset(
        data_vars={VAR_TEMPERATURE: ((COORD_TIME,), [25.0, 26.0])},
        coords={COORD_TIME: times},
    )

    issues = validator.validate_dataset(ds)
    issue_types = [i.issue_type for i in issues]
    assert "NON_MONOTONIC_TIME" in issue_types


def test_profiler_on_netcdf_file(tmp_path, synthetic_ocean_model_ds):
    nc_path = str(tmp_path / "test_model.nc")
    synthetic_ocean_model_ds.to_netcdf(nc_path)

    profiler = DatasetProfiler()
    profile = profiler.profile_netcdf_file(nc_path)

    assert profile["filename"] == "test_model.nc"
    assert profile["format"] == "NetCDF-4/HDF5"
    assert "open_time_sec" in profile["performance"]
    assert "slice_extraction_time_sec" in profile["performance"]
    assert profile["visualization_capabilities"]["temperature_depth_slices"] is True
    assert profile["visualization_capabilities"]["current_vector_visualization"] is True


def test_generate_validation_reports_infrastructure(tmp_path):
    data_dir = str(tmp_path / "data")
    docs_dir = str(tmp_path / "docs" / "data-validation")

    is_real = generate_validation_reports(data_dir=data_dir, output_dir=docs_dir)

    assert is_real is False
    assert os.path.exists(os.path.join(docs_dir, "dataset_compatibility_report.md"))
    assert os.path.exists(os.path.join(docs_dir, "dataset_profile.json"))
    assert os.path.exists(os.path.join(docs_dir, "model_observation_compatibility.md"))
    assert os.path.exists(os.path.join(docs_dir, "ml_readiness_report.md"))
    assert os.path.exists(os.path.join(docs_dir, "performance_report.md"))
