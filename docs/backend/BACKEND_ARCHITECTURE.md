# OceanTwin Backend Architecture Documentation

## Overview

The **OceanTwin Backend** is a high-performance Python/FastAPI scientific data access layer designed for the INCOIS 3D Ocean Digital Twin platform. It bridges raw scientific ocean datasets (NetCDF models, Argo in-situ observations, and 3D gridded monthly baselines) with frontend visualization engines and machine learning fusion services.

---

## Architectural Layers

```text
       Client / Frontend (3D Globe / REST Consumers)
                           │
                           ▼
                  FastAPI API Routers
  (/api/hycom, /api/argo, /api/baseline, /api/compare, /api/anomaly, /api/ocean)
                           │
                           ▼
                     Services Layer
  ┌──────────────────┬───────────────────┬─────────────────────┐
  │ HycomService     │ ArgoService       │ VAMBaselineService  │
  │ ComparisonService│ AnomalyService    │ OceanService (ML)   │
  └──────────────────┴───────────────────┴─────────────────────┘
                           │
                           ▼
                    Data Accessors
    (xarray lazy NetCDF reader, pandas in-memory indexer)
                           │
                           ▼
                    Real Datasets
  ┌────────────────────────────────────────────────────────────┐
  │ 1. RSMC_hycom_20260831.nc (~9.85 GB NetCDF Model)           │
  │ 2. ARGO_OceanTwin_clean.csv (1.469M Clean In-Situ Profiles)│
  │ 3. incois_argo_mnt_VAM.nc (61-Month 3D Gridded Baseline)   │
  └────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Configuration (`backend/api/config.py`)
Centralized Pydantic v2 `BaseSettings` (`APISettings`).
- `HYCOM_DATA_PATH`: Location of the 9.85 GB HYCOM NetCDF file.
- `ARGO_DATA_PATH`: Location of the 1.469M row cleaned Argo CSV.
- `ARGO_VAM_DATA_PATH`: Location of the 61-month gridded VAM baseline NetCDF.
- `MAX_SLICE_CELLS`: Response size cap (default: 250,000 cells) to prevent OOM errors.

### 2. Services Layer (`backend/api/services/`)
- **`HycomService`**: Lazy xarray accessor for HYCOM model variables (`TEMP`, `SALN`, `UVEL`, `VVEL`, `SSH`, `MLD`, `TCHP`). Features thread-safe LRU caching to prevent reloading the 9.85 GB file.
- **`ArgoService`**: High-performance pandas/numpy accessor for cleaned Argo float observations (`1,469,291` rows). Pre-indexes platforms and float cycles for sub-millisecond retrieval.
- **`VAMBaselineService`**: Climatological baseline accessor for INCOIS Monthly Gridded Argo VAM. Applies physical sanity masks (`-2.5 <= TEMP <= 40`, `2.0 <= SAL <= 41`) to convert land/bathymetry sentinels to `NaN`. Computes 5-year monthly means $\mu$ and standard deviations $\sigma$.
- **`ComparisonService`**: Matches HYCOM model predictions against Argo in-situ observations. Calculates spatial distance (Haversine km), depth delta (m), time delta (hours), and temperature/salinity prediction errors ($T_{model} - T_{obs}$).
- **`AnomalyService`**: Computes temperature/salinity anomalies ($\Delta T = T - \mu$) and Z-scores ($Z = \frac{T - \mu}{\sigma}$) against historical 5-year VAM monthly baselines.
- **`OceanService`**: Fused ML Ocean service combining predictions, observations, baselines, and 2D visualization slice extraction.

### 3. API Routers (`backend/api/routers/`)
- `health.py`: System health checks.
- `hycom.py`: `/api/hycom`, `/api/hycom/point`, `/api/hycom/profile`.
- `argo.py` (`observations.py`): `/api/argo`, `/api/argo/profile`, `/api/observations`.
- `baseline.py`: `/api/baseline`, `/api/baseline/point`, `/api/baseline/profile`.
- `compare.py`: `/api/compare`, `/api/anomaly`.
- `ocean.py`: `/api/ocean/point`, `/api/ocean/profile`, `/api/ocean/slice`, `/api/ocean/variables`.

---

## Memory & Performance Management

1. **Lazy Loading**: `xarray.open_dataset` opens NetCDF files without reading data arrays into RAM until specific indices are requested.
2. **In-Memory Caching**: Dataframes and dataset handles are cached across requests, eliminating disk I/O bottlenecks.
3. **Response Size Limits**: Enforces `MAX_SLICE_CELLS` to reject oversized 2D slice requests with explicit `HTTP 400 Bad Request`.
