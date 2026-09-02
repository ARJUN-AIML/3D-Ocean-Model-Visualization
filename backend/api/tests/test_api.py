"""
backend/api/tests/test_api.py
Comprehensive Integration Test Suite for FastAPI Layer.
Tests all endpoints against synthetic fixtures and real dataset services.
"""

import os
import numpy as np
import pytest
from fastapi.testclient import TestClient
import xarray as xr

from backend.api.main import app
from backend.api.dependencies import get_dataset_service
from backend.api.services.dataset_service import DatasetService


@pytest.fixture
def api_client(tmp_path, synthetic_ocean_model_ds: xr.Dataset):
    """
    TestClient fixture configured with a temporary data directory.
    Saves synthetic_ocean_model_ds into tmp_path / 'synthetic_model.nc'.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    nc_path = data_dir / "synthetic_model.nc"
    synthetic_ocean_model_ds.to_netcdf(str(nc_path))

    nan_ds = synthetic_ocean_model_ds.copy(deep=True)
    temp_arr = nan_ds["temperature"].values.copy()
    temp_arr[0, 0, 0, 0] = np.nan
    nan_ds["temperature"].values = temp_arr
    nan_path = data_dir / "nan_model.nc"
    nan_ds.to_netcdf(str(nan_path))

    service = DatasetService(data_dir=str(data_dir))
    app.dependency_overrides[get_dataset_service] = lambda: service

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    service.close_all_cached()


@pytest.fixture
def empty_api_client(tmp_path):
    """TestClient fixture configured with an empty data directory."""
    empty_dir = tmp_path / "empty_data"
    empty_dir.mkdir(parents=True, exist_ok=True)

    service = DatasetService(data_dir=str(empty_dir))
    app.dependency_overrides[get_dataset_service] = lambda: service

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    service.close_all_cached()


# 1. Health Endpoint
def test_health_endpoint(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "INCOIS" in data["service_name"]
    assert data["version"] == "1.0.0"


# 2. Empty Dataset Directory
def test_empty_dataset_directory(empty_api_client):
    response = empty_api_client.get("/api/datasets")
    assert response.status_code == 200
    data = response.json()
    assert data == []


# 3. Dataset Discovery
def test_dataset_discovery(api_client):
    response = api_client.get("/api/datasets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    ds_ids = [d["dataset_id"] for d in data]
    assert "synthetic_model.nc" in ds_ids


# 4. Dataset Metadata Detail
def test_dataset_metadata_detail(api_client):
    response = api_client.get("/api/datasets/synthetic_model.nc")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == "synthetic_model.nc"


# 5. Dataset Variables Listing
def test_dataset_variables_listing(api_client):
    response = api_client.get("/api/ocean/variables?dataset_id=synthetic_model.nc")
    assert response.status_code == 200
    data = response.json()
    var_names = [v["canonical_name"] for v in data]
    assert "temperature" in var_names


# 6. Valid Ocean Slice Request
def test_ocean_slice_valid(api_client):
    response = api_client.get(
        "/api/ocean/slice?dataset_id=synthetic_model.nc&variable=temperature&time=2024-01-01T00:00:00&depth=0.0"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == "synthetic_model.nc"


# 7. HYCOM Summary Endpoint
def test_hycom_summary_endpoint(api_client):
    response = api_client.get("/api/hycom")
    assert response.status_code == 200
    data = response.json()
    assert "INCOIS" in data["source"]
    assert data["timesteps_count"] == 28
    assert len(data["depth_levels"]) == 6


# 8. HYCOM Point Query
def test_hycom_point_endpoint(api_client):
    response = api_client.get(
        "/api/hycom/point?variable=temperature&time=2026-08-31T00:00:00Z&latitude=15.0&longitude=70.0&depth=10.0"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["variable"] == "TEMP"
    assert data["actual_depth"] == 10.0
    assert data["value"] is not None


# 9. HYCOM Profile Query
def test_hycom_profile_endpoint(api_client):
    response = api_client.get(
        "/api/hycom/profile?variable=temperature&time=2026-08-31T00:00:00Z&latitude=15.0&longitude=70.0"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["depths"]) == 6
    assert len(data["values"]) == 6


# 10. Argo Observations Query
def test_argo_observations_endpoint(api_client):
    response = api_client.get("/api/argo?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total_matched"] > 0
    assert len(data["observations"]) == 10
    obs = data["observations"][0]
    assert "platform_number" in obs
    assert "depth_m" in obs


# 11. Argo Profile Query
def test_argo_profile_endpoint(api_client):
    # Fetch first observation platform and cycle
    obs_res = api_client.get("/api/argo?limit=1").json()
    first_obs = obs_res["observations"][0]
    plat = first_obs["platform_number"]
    cyc = first_obs["cycle_number"]

    response = api_client.get(f"/api/argo/profile?platform_number={plat}&cycle_number={cyc}")
    assert response.status_code == 200
    data = response.json()
    assert data["platform_number"] == plat
    assert len(data["depths"]) > 0


# 12. VAM Baseline Summary Endpoint
def test_baseline_summary_endpoint(api_client):
    response = api_client.get("/api/baseline")
    assert response.status_code == 200
    data = response.json()
    assert data["timesteps_count"] == 61
    assert len(data["depth_levels"]) == 24


# 13. VAM Baseline Point Query
def test_baseline_point_endpoint(api_client):
    response = api_client.get("/api/baseline/point?variable=temperature&month=1&latitude=15.0&longitude=70.0&depth=5.0")
    assert response.status_code == 200
    data = response.json()
    assert data["month"] == 1
    assert data["baseline_mean"] is not None


# 14. VAM Baseline Profile Query
def test_baseline_profile_endpoint(api_client):
    response = api_client.get("/api/baseline/profile?variable=temperature&month=1&latitude=15.0&longitude=70.0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["depths"]) == 24
    assert len(data["baseline_means"]) == 24


# 15. Comparison Endpoint
def test_comparison_endpoint(api_client):
    # Get a real float profile to compare
    obs_res = api_client.get("/api/argo?limit=1").json()
    first_obs = obs_res["observations"][0]
    plat = first_obs["platform_number"]
    cyc = first_obs["cycle_number"]

    response = api_client.get(f"/api/compare?platform_number={plat}&cycle_number={cyc}")
    assert response.status_code == 200
    data = response.json()
    assert data["platform_number"] == plat
    assert "temperature_error" in data
    assert "matching_metadata" in data


# 16. Anomaly Endpoint
def test_anomaly_endpoint(api_client):
    response = api_client.get(
        "/api/anomaly?variable=temperature&value=28.5&time=2024-01-15T00:00:00Z&latitude=15.0&longitude=70.0&depth=5.0"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_value"] == 28.5
    assert data["baseline_mean"] is not None
    assert data["anomaly"] is not None


# 17. Fused Ocean Point Endpoint
def test_fused_ocean_point_endpoint(api_client):
    response = api_client.get(
        "/api/ocean/point?variable=temperature&time=2026-08-31T00:00:00Z&latitude=15.0&longitude=70.0&depth=10.0"
    )
    assert response.status_code == 200
    data = response.json()
    assert "hycom_model_value" in data
    assert "baseline_mean_value" in data
    assert "model_anomaly" in data


# 18. Fused Ocean Profile Endpoint
def test_fused_ocean_profile_endpoint(api_client):
    response = api_client.get(
        "/api/ocean/profile?variable=temperature&time=2026-08-31T00:00:00Z&latitude=15.0&longitude=70.0"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["hycom_profile"]["depths"]) == 6
    assert len(data["baseline_profile"]["depths"]) == 24
