"""
Unit tests for Indian Ocean Sample Generator and Ocean Dataset Manager.
"""

import os
from pathlib import Path
import pytest
import xarray as xr

from backend.science.sample_generator import generate_indian_ocean_demo_dataset, DEMO_DATA_STATUS
from backend.science.dataset_manager import OceanDatasetManager


def test_generate_indian_ocean_demo_dataset(tmp_path):
    demo_file = str(tmp_path / "demo_test.nc")
    ds = generate_indian_ocean_demo_dataset(output_path=demo_file, num_days=2)

    assert os.path.exists(demo_file)
    assert "temperature" in ds.data_vars
    assert "salinity" in ds.data_vars
    assert "u" in ds.data_vars
    assert "v" in ds.data_vars
    assert "density" in ds.data_vars
    assert ds.attrs["data_status"] == DEMO_DATA_STATUS
    assert ds.attrs["is_synthetic"] == "true"


def test_dataset_manager_fallback(tmp_path):
    mgr = OceanDatasetManager(data_root=str(tmp_path))

    # Calling get_or_create_default_dataset when empty should create indian_ocean_demo.nc
    ds, ds_id = mgr.get_or_create_default_dataset()

    assert ds_id == "indian_ocean_demo"
    assert isinstance(ds, xr.Dataset)

    prov = mgr.get_provenance_metadata(ds_id)
    assert prov["dataset_id"] == "indian_ocean_demo"
    assert prov["is_synthetic"] is True
    assert prov["data_status"] == DEMO_DATA_STATUS
    assert "temperature" in prov["variables"]
