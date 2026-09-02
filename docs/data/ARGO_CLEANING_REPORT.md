# OceanTwin — INCOIS Indian Argo Data Cleaning & Preparation Report

**Project**: OceanTwin / 3D Ocean Digital Twin Platform  
**Dataset**: INCOIS Indian Argo Floats (`data/argo/Indian_ARGO_Floats_fba1_2d9b_5c9d.csv`)  
**Processing Date**: 2026-09-02  

---

## 1. Input Dataset Overview

- **Original Filename**: `data/argo/Indian_ARGO_Floats_fba1_2d9b_5c9d.csv`
- **Data Source**: INCOIS ERDDAP Server (Indian Argo Floats Archive)
- **Columns Found in Raw File (16 columns)**:
  `PLATFORM_NUMBER`, `CYCLE_NUMBER`, `DIRECTION`, `time`, `JULD_QC`, `latitude`, `longitude`, `PRES_QC`, `PRES_ADJUSTED`, `PRES_ADJUSTED_QC`, `TEMP_QC`, `TEMP_ADJUSTED`, `TEMP_ADJUSTED_QC`, `PSAL_QC`, `PSAL_ADJUSTED`, `PSAL_ADJUSTED_QC`

---

## 2. Before Cleaning Statistics (Raw Dataset)

- **Total File Lines**: 1,471,410 (1 Header + 1 Units Metadata Row + 1,471,408 Observation Data Rows)
- **Total Observation Rows**: 1,471,408
- **Time Range**: `2020-01-01T10:59:39Z` to `2025-01-13T08:50:45Z`
- **Latitude Range**: `-29.872°` to `24.361°N`
- **Longitude Range**: `39.878°` to `93.228°E`
- **Pressure Range (`PRES_ADJUSTED`)**: `0.0 dbar` to `2047.0 dbar`
- **Temperature Range (`TEMP_ADJUSTED`)**: `-2.006 °C` to `32.2107 °C`
- **Salinity Range (`PSAL_ADJUSTED`)**: `24.97678 PSU` to `36.95492 PSU`
- **Missing Value Counts**: 0 missing values in required observation columns
- **Raw QC Flag Distribution**:
  - `PRES_ADJUSTED_QC`:
    - `1` (Good): 1,471,408 (100.0%)
  - `TEMP_ADJUSTED_QC`:
    - `1` (Good): 1,471,027 (99.974%)
    - `3` (Bad): 381 (0.026%)
  - `PSAL_ADJUSTED_QC`:
    - `1` (Good): 1,360,256 (92.446%)
    - `2` (Probably Good): 109,036 (7.410%)
    - `3` (Bad): 2,116 (0.144%)

---

## 3. Filtering & Removal Breakdown

| Filtering Step | Criteria / Condition | Rows Affected / Removed | Remaining Observations |
|---|---|---|---|
| **1. Units/Metadata Row Removal** | Line 1 containing ERDDAP unit strings (`UTC`, `decibar`, `degree_Celsius`, `PSU`, etc.) | **1 row** | 1,471,408 |
| **2. Missing Required Fields** | Nulls in `time`, `latitude`, `longitude`, `PRES_ADJUSTED`, `TEMP_ADJUSTED`, or `PSAL_ADJUSTED` | **0 rows** | 1,471,408 |
| **3. QC Flag Filtering** | `PRES_ADJUSTED_QC = 3`, `TEMP_ADJUSTED_QC = 3`, or `PSAL_ADJUSTED_QC = 3` | **2,117 unique rows** (381 TEMP_QC=3, 2,116 PSAL_QC=3) | 1,469,291 |
| **4. Physical Pressure Limits** | `PRES_ADJUSTED < 0` or `PRES_ADJUSTED > 12000 dbar` | **0 rows** | 1,469,291 |
| **5. Physical Temperature Limits** | `TEMP_ADJUSTED < -2.5` or `TEMP_ADJUSTED > 40.0 °C` | **0 rows** | 1,469,291 |
| **6. Physical Salinity Limits** | `PSAL_ADJUSTED < 2.0` or `PSAL_ADJUSTED > 41.0 PSU` | **0 rows** | 1,469,291 |
| **7. Spatial Coordinate Limits** | `latitude` outside `[-90, 90]` or `longitude` outside `[-180, 180]` | **0 rows** | 1,469,291 |
| **Unexpected QC Flags** | Flags other than `{1, 2, 3}` | **0 rows** | 1,469,291 |

---

## 4. After Cleaning Statistics (Final Clean Dataset)

- **Final Row Count**: **1,469,291 observations**
- **Time Range**: `2020-01-01T10:59:39Z` to `2025-01-13T08:50:45Z`
- **Latitude Range**: `-29.872°` to `24.361°N`
- **Longitude Range**: `39.878°` to `93.228°E`
- **Pressure Range (`PRES_ADJUSTED`)**: `0.0 dbar` to `2047.0 dbar`
- **Depth Range (`depth_m`)**: `0.0 m` to `2025.2501 m`
- **Temperature Range (`TEMP_ADJUSTED`)**: `-2.006 °C` to `32.2107 °C`
- **Salinity Range (`PSAL_ADJUSTED`)**: `24.97678 PSU` to `36.95492 PSU`
- **Final QC Flag Distributions**:
  - `PRES_ADJUSTED_QC`:
    - `1` (Good): 1,469,291 (100.0%)
  - `TEMP_ADJUSTED_QC`:
    - `1` (Good): 1,469,291 (100.0%)
  - `PSAL_ADJUSTED_QC`:
    - `1` (Good): 1,360,255 (92.578%)
    - `2` (Probably Good): 109,036 (7.422%)

---

## 5. Output File

- **Path**: `data/argo/ARGO_OceanTwin_clean.csv`
- **Final Columns (12 columns)**:
  1. `PLATFORM_NUMBER`
  2. `CYCLE_NUMBER`
  3. `time`
  4. `latitude`
  5. `longitude`
  6. `PRES_ADJUSTED`
  7. `PRES_ADJUSTED_QC`
  8. `TEMP_ADJUSTED`
  9. `TEMP_ADJUSTED_QC`
  10. `PSAL_ADJUSTED`
  11. `PSAL_ADJUSTED_QC`
  12. `depth_m`

---

## 6. Scientific Notes & Justification

1. **Usage of Adjusted Variables (`PRES_ADJUSTED`, `TEMP_ADJUSTED`, `PSAL_ADJUSTED`)**:
   Argo delayed-mode and real-time processing pipelines perform post-deployment sensor drift calibration, pressure axis alignment, and thermal mass corrections. `_ADJUSTED` fields represent the scientifically corrected observations certified by INCOIS and the International Argo Program.
2. **Quality Control (QC) Flag Retention & Filtering Strategy**:
   - `QC 1` (Good Data) and `QC 2` (Probably Good Data) are retained. In oceanography, QC 2 measurements are valid for quantitative modeling.
   - `QC 3` (Bad Data / Correctable) is strictly removed.
   - QC flags are preserved alongside measurements in the output schema to maintain complete traceability for downstream ML weighting.
3. **Physical Range Filtering**:
   Oceanographic envelope boundaries ($\text{TEMP} \in [-2.5, 40]^\circ\text{C}$, $\text{PSAL} \in [2, 41]\text{ PSU}$, $\text{PRES} \in [0, 12000]\text{ dbar}$) were enforced as non-destructive sanity barriers to prevent unphysical sensor glitches from entering downstream neural networks.
4. **Pressure-to-Depth Conversion Methodology**:
   Pressure (dbar) is converted to vertical depth in meters ($Z$) using the Saunders & Fofonoff (1981) / UNESCO (1983) formula:
   $$g(\phi) = 9.780318 \cdot (1.0 + (5.2788 \times 10^{-3} + 2.36 \times 10^{-5} \sin^2 \phi) \sin^2 \phi)$$
   $$depth\_m = \frac{9.72659 \cdot P - 2.2512 \times 10^{-5} P^2 + 2.279 \times 10^{-10} P^3 - 1.82 \times 10^{-15} P^4}{g(\phi) + 1.092 \times 10^{-6} P}$$
   This accounts for latitude-dependent gravitational variations and seawater density compression without assuming a simplistic $1 \text{ dbar} = 1 \text{ m}$ shortcut. `PRES_ADJUSTED` is retained intact alongside `depth_m`.
