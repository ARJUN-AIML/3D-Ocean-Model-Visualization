# OceanTwin Backend REST API Specification

**Platform**: OceanTwin / INCOIS 3D Ocean Digital Twin  
**Base URL**: `http://localhost:8000/api`  
**API Documentation**: `http://localhost:8000/docs` (Swagger UI), `http://localhost:8000/redoc` (ReDoc)  
**OpenAPI Specification**: `http://localhost:8000/openapi.json`  

---

## 1. System Health

### `GET /health`
Returns system status, service name, and API version.

#### Response `200 OK`:
```json
{
  "status": "ok",
  "service_name": "INCOIS 3D Ocean Data Access Layer",
  "version": "1.0.0"
}
```

---

## 2. HYCOM Model Data Endpoints

### `GET /api/hycom`
Returns HYCOM dataset metadata, dimensions, time range, depth levels, coordinate bounds, and variable inventory.

#### Response `200 OK`:
```json
{
  "dataset_id": "RSMC_hycom_20260831.nc",
  "source": "INCOIS RSMC HYCOM",
  "file_size_mb": 10091.45,
  "timesteps_count": 28,
  "time_start": "2026-08-30T06:00:00Z",
  "time_end": "2026-09-06T00:00:00Z",
  "depth_levels": [0.0, 10.0, 50.0, 100.0, 250.0, 500.0],
  "lat_min": -44.929962,
  "lat_max": 30.954096,
  "lon_min": 20.0,
  "lon_max": 119.839996,
  "variables": [
    {"name": "TEMP", "long_name": "Water Temperature", "units": "degC", "dimensions": ["TIME", "DEPTH", "LAT", "LON"], "shape": [28, 6, 1384, 1665]},
    {"name": "SALN", "long_name": "Water Salinity", "units": "PSU", "dimensions": ["TIME", "DEPTH", "LAT", "LON"], "shape": [28, 6, 1384, 1665]}
  ]
}
```

### `GET /api/hycom/point`
Extracts nearest point value for a specific HYCOM variable.

#### Query Parameters:
- `variable` (string, default: `"temperature"`): Variable (`temperature`, `salinity`, `u`, `v`, `ssh`, `mld`, `tchp`).
- `time` (string, required): ISO8601 timestamp (e.g. `2026-08-31T00:00:00Z`).
- `latitude` (float, required): Latitude (-90 to 90).
- `longitude` (float, required): Longitude (-180 to 180).
- `depth` (float, default: `0.0`): Depth in meters (0 to 12000).

#### Response `200 OK`:
```json
{
  "source": "INCOIS RSMC HYCOM",
  "variable": "TEMP",
  "units": "degC",
  "requested_time": "2026-08-31T00:00:00Z",
  "actual_time": "2026-08-31T00:00:00Z",
  "requested_latitude": 15.0,
  "actual_latitude": 15.01,
  "requested_longitude": 70.0,
  "actual_longitude": 70.02,
  "requested_depth": 10.0,
  "actual_depth": 10.0,
  "value": 28.345
}
```

### `GET /api/hycom/profile`
Extracts vertical depth profile across available HYCOM depth levels at a lat/lon location.

#### Query Parameters:
- `variable` (string, default: `"temperature"`): Variable (`temperature`, `salinity`, `u`, `v`).
- `time` (string, required): ISO8601 timestamp.
- `latitude` (float, required): Latitude (-90 to 90).
- `longitude` (float, required): Longitude (-180 to 180).

#### Response `200 OK`:
```json
{
  "source": "INCOIS RSMC HYCOM",
  "variable": "TEMP",
  "units": "degC",
  "requested_time": "2026-08-31T00:00:00Z",
  "actual_time": "2026-08-31T00:00:00Z",
  "requested_latitude": 15.0,
  "actual_latitude": 15.01,
  "requested_longitude": 70.0,
  "actual_longitude": 70.02,
  "depths": [0.0, 10.0, 50.0, 100.0, 250.0, 500.0],
  "values": [28.5, 28.3, 24.1, 19.8, 12.4, 7.2]
}
```

---

## 3. Argo Observation Endpoints

### `GET /api/argo`
Queries cleaned INCOIS Indian Argo float observations with spatial/temporal/platform filtering.

#### Query Parameters:
- `platform_number` (string, optional): Float WMO ID (e.g. `2901307`).
- `cycle_number` (int, optional): Profile cycle index (e.g. `322`).
- `lat_min`, `lat_max` (float, optional): Latitude bounding box.
- `lon_min`, `lon_max` (float, optional): Longitude bounding box.
- `depth_min`, `depth_max` (float, optional): Depth bounding box in meters.
- `time_start`, `time_end` (string, optional): ISO8601 time window.
- `limit` (int, default: `100`): Max records (1-10000).
- `offset` (int, default: `0`): Pagination offset.

#### Response `200 OK`:
```json
{
  "source": "INCOIS Indian Argo Floats (Cleaned)",
  "total_matched": 1469291,
  "limit": 100,
  "offset": 0,
  "observations": [
    {
      "platform_number": "2901307",
      "cycle_number": 322,
      "time": "2020-01-01T10:59:39Z",
      "latitude": 8.145,
      "longitude": 66.665,
      "pressure_adjusted": 4.6,
      "pressure_qc": 1,
      "temperature_adjusted": 29.31,
      "temperature_qc": 1,
      "salinity_adjusted": 34.89756,
      "salinity_qc": 1,
      "depth_m": 4.557
    }
  ]
}
```

### `GET /api/argo/profile`
Retrieves full vertical profile for a single float cycle.

#### Query Parameters:
- `platform_number` (string, required): Float WMO ID.
- `cycle_number` (int, required): Profile cycle index.

---

## 4. Monthly Baseline (VAM) Endpoints

### `GET /api/baseline`
Returns Monthly Gridded Argo VAM baseline summary, depth levels (24 levels), and coverage.

### `GET /api/baseline/point`
Queries historical 5-year climatological baseline mean and std for a specific month (1-12), location, and depth.

### `GET /api/baseline/profile`
Queries vertical baseline profile across all 24 VAM depth levels (5m to 2000m).

---

## 5. Model-Observation Comparison & Anomaly Endpoints

### `GET /api/compare`
Compares HYCOM model prediction against an Argo float profile observation.
Returns matched values, temperature error ($T_{model} - T_{obs}$), salinity error ($S_{model} - S_{obs}$), current vectors, and spatial distance metrics.

### `GET /api/anomaly`
Calculates ocean temperature or salinity anomaly ($\Delta = value - baseline\_mean$) and Z-score ($Z = \frac{value - mean}{std}$) against historical 5-year INCOIS VAM monthly baseline.

---

## 6. Fused Digital Twin Endpoints

### `GET /api/ocean/point`
Combines HYCOM model prediction, VAM historical baseline, and calculated anomaly into a unified point payload.

### `GET /api/ocean/profile`
Combines HYCOM model vertical profile and VAM baseline profile across depth levels.

### `GET /api/ocean/slice`
Extracts a 2D depth/time slice grid array for 3D visualization.

---

## 7. Error Handling

Standard HTTP status codes:
- `400 Bad Request`: Invalid parameter bounds, invalid ISO8601 date, or slice exceeding `MAX_SLICE_CELLS`.
- `404 Not Found`: Non-existent dataset, variable, float platform, or profile cycle.
- `422 Unprocessable Entity`: Request query validation failure.
- `500 Internal Server Error`: Generic internal error without stack trace leaks.
