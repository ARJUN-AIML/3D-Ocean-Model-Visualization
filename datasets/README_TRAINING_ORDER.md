# OceanTwin 3D — Synthetic Data & Training Order

## IMPORTANT
All CSV files in this package are **synthetic/demo data** generated to test the OceanTwin pipeline.
They are NOT INCOIS/HYCOM/Argo measurements and must never be presented as real scientific validation.

## Files

### 01_matched_model_argo_training.csv
Primary ML + validation dataset.
Contains paired synthetic numerical-model values and synthetic Argo-like observations.
Use it for:
- XGBoost temperature bias correction
- XGBoost salinity bias correction
- MAE / RMSE / Bias / R² / Pearson Correlation
- raw vs corrected comparison
- error heatmap
- reliability logic
- chronological 70/15/15 train/validation/test split

Target definitions:
- temp_error_obs_minus_model_c = obs_temp_c - model_temp_c
- sal_error_obs_minus_model_psu = obs_salinity_psu - model_salinity_psu

Corrected value:
- corrected_temp = model_temp_c + predicted_temp_error
- corrected_salinity = model_salinity_psu + predicted_salinity_error

### 02_ocean_model_grid_samples.csv
Synthetic numerical-ocean-model-like samples.
Use it for:
- 3D temperature layer
- salinity layer
- current arrows / current particles
- vertical profile
- time/depth filtering
- chlorophyll demo
- sea-surface-height demo

### 03_argo_observations.csv
Synthetic Argo-like observations.
Use it for:
- Argo markers
- float/profile popups
- vertical profiles
- model-vs-observation comparison

### 04_climatology_baseline.csv
Monthly region/depth baseline means and standard deviations.
Use it for:
- anomaly Z-scores for temperature, salinity and current speed
- NORMAL / WATCH / WARNING / CRITICAL demo classification

Recommended:
z = (current_value - climatology_mean) / climatology_std

Thresholds should be treated as configurable demo thresholds, not universal scientific standards.

### 05_current_vectors_trajectory.csv
Regular Bay of Bengal current-vector field.
Use it for:
- animated current particles
- current arrows
- Current Trajectory Simulation
- interpolation testing

Input shape is compatible with:
{ lat, lon, u, v }
and also contains timestamp/depth for future 4D use.

### 06_wave_samples.csv
Optional synthetic wave data.
Use it for:
- wave-height visualization
- wave direction
- wave period

No ML training is required for this file.

## Correct build/training order

1. **Load and validate CSVs**
   - check missing values
   - ranges
   - units
   - timestamps
   - QC fields
   - duplicate records

2. **Build model-vs-observation matching/validation**
   Start with `01_matched_model_argo_training.csv`.
   Compute raw:
   - error = observation - model
   - MAE
   - RMSE
   - mean signed Bias
   - R²
   - Pearson Correlation
   - number of matched observations / coverage

3. **Train XGBoost temperature bias model**
   Input features:
   - lat
   - lon
   - depth_m
   - month_sin
   - month_cos
   - model_temp_c
   - model_salinity_psu
   - u_ms
   - v_ms
   - current_speed_ms

   Target:
   `temp_error_obs_minus_model_c`

4. **Evaluate temperature correction only on TEST rows**
   `corrected_temp = model_temp_c + predicted_error`

   Compare RAW vs CORRECTED using:
   - MAE
   - RMSE
   - Bias
   - R²
   - Correlation

5. **Train XGBoost salinity bias model**
   Same feature set.
   Target:
   `sal_error_obs_minus_model_psu`

6. **Evaluate salinity correction**
   Same held-out-test procedure.

7. **Build Error Heatmap**
   Use matched points.
   Color by:
   - raw temp error
   - corrected temp error
   - raw salinity error
   - corrected salinity error

8. **Build Reliability Status**
   Do NOT train a fake accuracy model.
   Derive reliability using:
   - observation count
   - QC
   - matching distance/time gap
   - validation error
   - spatial coverage

   Suggested labels:
   HIGH / MODERATE / LOW / INSUFFICIENT

9. **Build anomaly engine**
   Use `04_climatology_baseline.csv`.
   Compare current model values to matching:
   - region
   - month
   - depth
   baseline.

10. **Connect Cesium ocean visualization**
    Use `02_ocean_model_grid_samples.csv` for:
    - temperature
    - salinity
    - currents
    - profiles
    - time/depth controls

11. **Connect Argo layer**
    Use `03_argo_observations.csv`.

12. **Current particles + trajectory**
    Use `05_current_vectors_trajectory.csv`.
    Interpolate `u,v` around the selected start point and step the position through time.
    Call this a **current-based estimated trajectory**, not an exact prediction.

13. **Wave layer (optional)**
    Use `06_wave_samples.csv`.

14. **AI Explain Region / Report Generator**
    No separate ML training dataset is required.
    Feed only verified backend results such as:
    - selected region
    - time/depth
    - model values
    - observations
    - validation metrics
    - reliability
    - detected anomalies
    - trajectory summary

    The language model should explain these facts, not invent scientific values.

## Move from synthetic → real data later

Replace only the data adapters:

Real INCOIS/HYCOM model output
        ↓
same canonical fields

Real Argo profiles
        ↓
same observation fields

Model-Argo matcher
        ↓
same matched-training schema

Therefore the frontend, metrics, XGBoost training pipeline, error heatmap,
reliability engine, anomaly engine and trajectory UI do not need to be redesigned.

## Recommended commands

Create environment:
```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

Install:
```bash
pip install pandas numpy scikit-learn xgboost joblib
```

Train:
```bash
python train_bias_models.py
```

## SIH presentation wording

Correct:
> "The current prototype uses clearly labelled synthetic data to validate the end-to-end pipeline. The architecture is designed to replace these adapters with real INCOIS/HYCOM and Argo datasets."

Do NOT say:
> "These synthetic results prove real ocean-model accuracy."
