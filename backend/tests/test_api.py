"""
backend/tests/test_api.py
FastAPI API bridge contract and integration tests using TestClient.
Verifies response schemas, status codes, camelCase property mappings, and CORS behavior.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["is_real_data_connected"] is True
    assert "provenance_mode" in data


def test_datasets_list():
    response = client.get("/api/datasets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "spatial_bounds" in data[0]


def test_slice_endpoint():
    response = client.get("/api/slice?variable=temp&depth=0")
    assert response.status_code == 200
    data = response.json()
    assert "datasetId" in data
    assert data["variable"] == "temp"
    assert "values" in data
    assert "latitudes" in data
    assert "longitudes" in data


def test_vectors_endpoint():
    response = client.get("/api/vectors?depth=0&stride=1")
    assert response.status_code == 200
    data = response.json()
    assert "vectorCount" in data
    assert "vectors" in data
    if data["vectorCount"] > 0:
        first = data["vectors"][0]
        assert "lat" in first
        assert "lon" in first
        assert "u" in first
        assert "v" in first
        assert "speed" in first


def test_observations_list():
    response = client.get("/api/observations?instrument_type=argo")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "wmoNumber" in first
    assert "profileData" in first
    assert "qualityStatus" in first


def test_observation_profile():
    response = client.get("/api/observations/ARGO_2901234/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ARGO_2901234"
    assert "profileData" in data


def test_bias_predict_endpoint():
    payload = {
        "targetVariable": "temp",
        "sensorType": "argo",
        "modelTemperature": 28.5,
        "modelSalinity": 35.0,
        "depth": 10.0,
        "latitude": 15.42,
        "longitude": 68.12
    }
    response = client.post("/api/bias/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "rawValue" in data
    assert "correctedValue" in data
    assert "mlModelName" in data


def test_validation_metrics_endpoint():
    response = client.get("/api/validation/metrics?variable=temp")
    assert response.status_code == 200
    data = response.json()
    assert "mae" in data
    assert "rmse" in data
    assert "r2" in data
    assert data["isBackendConnected"] is True


def test_anomalies_endpoint():
    response = client.get("/api/anomalies?variable=temp")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "zScore" in data[0]
    assert "severity" in data[0]


def test_trajectory_endpoint():
    response = client.get("/api/trajectory?startLat=15.42&startLon=68.12&durationHours=24")
    assert response.status_code == 200
    data = response.json()
    assert data["startLat"] == 15.42
    assert "path" in data
    assert len(data["path"]) > 0


def test_cors_configuration():
    response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
