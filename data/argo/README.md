# OceanTwin — Argo Dataset Provenance & Metadata

## Dataset Summary

- **Dataset Name**: INCOIS Indian Ocean Argo Float Observation Profiles
- **Source Organization**: Indian National Centre for Ocean Information Services (INCOIS / MoES)
- **Source Type**: In-situ Profiling Argo Floats (Indian Ocean Domain)
- **Source URL**: INCOIS ERDDAP Data Server
- **Raw Input Filename**: `data/argo/Indian_ARGO_Floats_fba1_2d9b_5c9d.csv`
- **Cleaned Output Filename**: `data/argo/ARGO_OceanTwin_clean.csv`
- **Processing Script**: `scripts/argo/clean_argo.py`
- **Cleaning Report**: `docs/data/ARGO_CLEANING_REPORT.md`
- **Processing Date**: 2026-09-02

---

## Cleaning & Filtering Protocol

1. **Units Row Removal**:
   Line 1 metadata row containing ERDDAP unit strings (`UTC`, `decibar`, `degree_Celsius`, `PSU`, etc.) detected and removed.
2. **Variable Selection**:
   Preserved adjusted physical measurements (`PRES_ADJUSTED`, `TEMP_ADJUSTED`, `PSAL_ADJUSTED`) and corresponding quality flags (`PRES_ADJUSTED_QC`, `TEMP_ADJUSTED_QC`, `PSAL_ADJUSTED_QC`).
3. **QC Filter**:
   - **Retained**: QC flags `1` (Good) and `2` (Probably Good).
   - **Removed**: QC flag `3` (Bad data).
4. **Physical Limits**:
   - `0 <= PRES_ADJUSTED <= 12000` (dbar)
   - `-2.5 <= TEMP_ADJUSTED <= 40.0` (°C)
   - `2.0 <= PSAL_ADJUSTED <= 41.0` (PSU)
   - `-90 <= latitude <= 90` (°N)
   - `-180 <= longitude <= 180` (°E)
5. **Depth Approximation (`depth_m`)**:
   Calculated from `PRES_ADJUSTED` and `latitude` using Saunders & Fofonoff (1981) / UNESCO (1983) oceanographic hydrostatic pressure conversion.

---

## Column Schema (`ARGO_OceanTwin_clean.csv`)

| Column Name | Type | Description |
|---|---|---|
| `PLATFORM_NUMBER` | string | Unique WMO Float Identifier (e.g. `2901307`) |
| `CYCLE_NUMBER` | integer | Profile cycle index number |
| `time` | string (ISO 8601 UTC) | Timestamp of profile observation (`YYYY-MM-DDTHH:MM:SSZ`) |
| `latitude` | float64 | WGS84 Latitude coordinate (decimal degrees north) |
| `longitude` | float64 | WGS84 Longitude coordinate (decimal degrees east) |
| `PRES_ADJUSTED` | float64 | Adjusted sea water hydrostatic pressure (decibar) |
| `PRES_ADJUSTED_QC` | integer | Quality flag for adjusted pressure (1=Good, 2=Probably Good) |
| `TEMP_ADJUSTED` | float64 | Adjusted sea water temperature (°C) |
| `TEMP_ADJUSTED_QC` | integer | Quality flag for adjusted temperature (1=Good, 2=Probably Good) |
| `PSAL_ADJUSTED` | float64 | Adjusted sea water practical salinity (PSU) |
| `PSAL_ADJUSTED_QC` | integer | Quality flag for adjusted salinity (1=Good, 2=Probably Good) |
| `depth_m` | float64 | UNESCO 1983 calculated depth in meters (positive down) |
