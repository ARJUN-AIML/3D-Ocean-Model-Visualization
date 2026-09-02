# OceanTwin — INCOIS RSMC HYCOM NetCDF Scientific Analysis Report

**Project**: OceanTwin / 3D Ocean Digital Twin Platform  
**File Analyzed**: `data/hycom/RSMC_hycom_20260831.nc`  
**File Size**: 10,091.45 MB (9.85 GB)  
**Analysis Date**: 2026-09-02  

---

## 1. File Identification & Overview

- **Dataset Name**: INCOIS RSMC HYCOM Ocean Model Analysis & Forecast Output
- **Source / Institution**: INCOIS (Indian National Centre for Ocean Information Services) / RSMC
- **Model Name**: HYCOM (Hybrid Coordinate Ocean Model)
- **Export Tool**: PyFerret V7.63 (optimized) 31-Aug-26
- **CF Conventions**: `CF-1.6`
- **Data Type**: Gridded 4D Hydrographic & Current Velocity Fields (`TIME` × `DEPTH` × `LAT` × `LON`)
- **Status**: Operational Real-Time Short-Term Analysis/Forecast

---

## 2. Dataset Dimensions & Grid Resolution

### Dimensions
- `TIME`: **28 time steps** (6-hourly resolution over 7 days)
- `DEPTH`: **6 vertical levels** (`0.0m`, `10.0m`, `50.0m`, `100.0m`, `250.0m`, `500.0m`)
- `LAT`: **1,384 grid points** (Range: `-44.930°S` to `30.954°N`, spacing ~`0.055°` / ~6.1 km)
- `LON`: **1,665 grid points** (Range: `20.000°E` to `119.840°E`, spacing `0.060°` / ~6.67 km)
- `bnds`: **2** (Coordinate boundary bounds)

### Grid Resolution
- **Horizontal Resolution**: High-resolution regional grid of approximately **1/16° (~6 km)**.
- **Vertical Resolution**: 6 discrete depth levels covering the upper ocean column (`0 m` to `500 m`).

---

## 3. Coordinates Summary

| Coordinate | Standard Name | Size | Min Value | Max Value | Units / Description |
|---|---|---|---|---|---|
| `TIME` | `time` | 28 | `2026-08-30T06:00:00Z` | `2026-09-06T00:00:00Z` | 6-hourly UTC timestamps |
| `DEPTH` | `depth` | 6 | `0.0` | `500.0` | Depth in meters below surface |
| `LAT` | `latitude` | 1384 | `-44.92996°` | `30.95410°` | WGS84 Decimal degrees north |
| `LON` | `longitude` | 1665 | `20.00000°` | `119.84000°` | WGS84 Decimal degrees east |

---

## 4. Scientific Variables Inventory

| Variable | Long Name | Dimensions | Shape | Units | Min Value | Max Value | Fill Value | Classification |
|---|---|---|---|---|---|---|---|---|
| `TEMP` | Water Temperature | (`TIME`, `DEPTH`, `LAT`, `LON`) | (28, 6, 1384, 1665) | °C | `2.8073` | `36.0078` | `-9.9999998e+33` | **REQUIRED** |
| `SALN` | Water Salinity | (`TIME`, `DEPTH`, `LAT`, `LON`) | (28, 6, 1384, 1665) | PSU | `2.5301` | `42.1652` | `-9.9999998e+33` | **REQUIRED** |
| `SSH` | Sea Surface Height | (`TIME`, `LAT`, `LON`) | (28, 1384, 1665) | m | `-0.8620` | `1.8931` | `1.2676506e+30` | **USEFUL** |
| `UVEL` | Eastward Current Velocity | (`TIME`, `DEPTH`, `LAT`, `LON`) | (28, 6, 1384, 1665) | m/s | `-2.4195` | `2.6102` | `1.2676506e+30` | **USEFUL** |
| `VVEL` | Northward Current Velocity | (`TIME`, `DEPTH`, `LAT`, `LON`) | (28, 6, 1384, 1665) | m/s | `-2.8616` | `3.1509` | `1.2676506e+30` | **USEFUL** |
| `MLD` | Mixed Layer Depth (Density) | (`TIME`, `LAT`, `LON`) | (28, 1384, 1665) | m | `0.4085` | `199.9999` | `-1.0e+34` | **USEFUL** |
| `TCHP` | Tropical Cyclone Heat Potential | (`TIME`, `LAT`, `LON`) | (28, 1384, 1665) | kJ/cm² | `0.0000` | `263.5743` | `-1.0e+34` | **USEFUL** |
| `TEMP_CT` | TEOS-10 Conservative Temp | (`TIME`, `DEPTH`, `LAT`, `LON`) | (28, 6, 1384, 1665) | °C | `2.7786` | `35.7014` | `-9.9999998e+33` | NOT NEEDED NOW |
| `SALNA` | TEOS-10 Absolute Salinity | (`TIME`, `DEPTH`, `LAT`, `LON`) | (28, 6, 1384, 1665) | g/kg | `2.5421` | `42.3641` | `-9.9999998e+33` | NOT NEEDED NOW |

---

## 5. Argo vs HYCOM Compatibility Analysis

| Feature | Cleaned Argo Observations (`ARGO_OceanTwin_clean.csv`) | RSMC HYCOM NetCDF (`RSMC_hycom_20260831.nc`) | Compatible? | Explanation |
|---|---|---|---|---|
| **Time Coverage** | `2020-01-01` to `2025-01-13` | `2026-08-30` to `2026-09-06` | **NO** | **1.5+ year gap**. HYCOM file contains real-time 2026 forecast data; Argo contains historical 2020-2025 data. |
| **Latitude Range** | `-29.872°` to `24.361°N` | `-44.930°` to `30.954°N` | **YES** | HYCOM spatial domain completely covers Argo latitude range. |
| **Longitude Range** | `39.878°` to `93.228°E` | `20.000°` to `119.840°E` | **YES** | HYCOM spatial domain completely covers Argo longitude range. |
| **Depth Range** | `0.0` to `2025.25 m` (continuous) | `0, 10, 50, 100, 250, 500 m` (6 levels) | **PARTIALLY** | Covers upper ocean column (`0-500 m`). Deeper layers (`500-2000 m`) are not present in this HYCOM file. |
| **Temperature** | `-2.006°C` to `32.2107°C` | `2.8073°C` to `36.0078°C` | **YES** | Standard temperature variable (`TEMP`) available in °C. |
| **Salinity** | `24.97678` to `36.95492 PSU` | `2.5301` to `42.1652 PSU` | **YES** | Standard salinity variable (`SALN`) available in PSU. |

---

## 6. Suitability Verdicts

1. **Suitable for OceanTwin 3D Visualization?**  
   **YES.** Excellent dataset for rendering high-resolution 3D temperature/salinity depth slices, sea surface height topography, mixed layer depth, and 3D current vector advection (`UVEL`/`VVEL`).
2. **Suitable for Model-Observation Comparison Pipeline Development?**  
   **YES.** Perfect structural test file for building NetCDF ingestion adapters, 3D grid interpolation modules, and FastAPI endpoints.
3. **Suitable for Direct Comparison with Current 2020–2025 Argo Dataset?**  
   **NO.** Contains 2026 real-time forecast data (`2026-08-30` to `2026-09-06`). No time overlap exists with historical Argo observations (`2020` to `2025`).
4. **Suitable as a Test Dataset for Pipeline Architecture?**  
   **YES.** Serves as an ideal blueprint for the HYCOM processing and API pipeline.

---

## 7. Recommended Next Step

**Pipeline Strategy**:
1. Use `RSMC_hycom_20260831.nc` as the target file to develop and test the HYCOM NetCDF processing pipeline, 3D slice extractor, and current vector generator.
2. Acquire historical INCOIS HYCOM reanalysis/analysis NetCDF files covering `2020–2025` from INCOIS THREDDS / ERDDAP for ML training and model-observation matching.
