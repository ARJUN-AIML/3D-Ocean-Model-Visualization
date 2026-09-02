"""
scripts/argo/clean_argo.py
OceanTwin — INCOIS Indian Argo Data Cleaning & Preparation Script.

Reads raw INCOIS ERDDAP Argo Float CSV data, validates coordinate/measurement ranges,
performs QC filtering (removes QC 3 bad data), calculates approximate depth from pressure
using the UNESCO (1983) / Saunders & Fofonoff (1981) formula, and exports a clean dataset
for OceanTwin downstream digital twin processing.
"""

import os
import sys
import pandas as pd
import numpy as np


def pressure_to_depth_unesco1983(pressure_dbar: np.ndarray, latitude_deg: np.ndarray) -> np.ndarray:
    """
    Converts hydrostatic pressure (dbar) to depth (meters) using Saunders & Fofonoff (1981) / UNESCO (1983) formula.

    Formula:
      x = sin(latitude * pi / 180)^2
      g(lat) = 9.780318 * (1.0 + (5.2788e-3 + 2.36e-5 * x) * x)
      num = 9.72659 * P - 2.2512e-5 * P^2 + 2.279e-10 * P^3 - 1.82e-15 * P^4
      den = g(lat) + 1.092e-6 * P
      depth_m = num / den
    """
    x = np.sin(np.radians(latitude_deg)) ** 2
    g_lat = 9.780318 * (1.0 + (5.2788e-3 + 2.36e-5 * x) * x)
    num = 9.72659 * pressure_dbar - 2.2512e-5 * (pressure_dbar ** 2) + 2.279e-10 * (pressure_dbar ** 3) - 1.82e-15 * (pressure_dbar ** 4)
    den = g_lat + 1.092e-6 * pressure_dbar
    return num / den


def clean_argo_dataset(input_csv: str, output_csv: str):
    print("==================================================================")
    print("OceanTwin — INCOIS Indian Argo Data Cleaning Pipeline")
    print("==================================================================")
    print(f"Input file:  {input_csv}")
    print(f"Output file: {output_csv}\n")

    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input file not found at: {input_csv}")

    # 1. Read Raw CSV
    df_raw = pd.read_csv(input_csv, header=0, low_memory=False)
    total_raw_rows = len(df_raw)
    print(f"1. Total raw file rows (including header/units): {total_raw_rows + 1}")
    print(f"   Raw DataFrame rows:                       {total_raw_rows}")

    # 2. Units Row Detection & Removal
    first_row = df_raw.iloc[0]
    unit_keywords = {'UTC', 'degrees_north', 'degrees_east', 'decibar', 'degree_Celsius', 'PSU'}
    is_units_row = any(val in unit_keywords for val in first_row.values if isinstance(val, str))

    if is_units_row:
        units_row_removed = 1
        df_data = df_raw.iloc[1:].copy()
        print("   Detected units/metadata row immediately after header. Removed: 1 row.")
    else:
        units_row_removed = 0
        df_data = df_raw.copy()
        print("   No units row detected. Preserved all rows.")

    obs_input_rows = len(df_data)
    print(f"   Input observation rows to process:        {obs_input_rows}")

    # 3. Data Type Conversions
    print("\n2. Converting data types...")
    df_data['PLATFORM_NUMBER'] = df_data['PLATFORM_NUMBER'].astype(str).str.replace(r'\.0$', '', regex=True)
    df_data['CYCLE_NUMBER'] = pd.to_numeric(df_data['CYCLE_NUMBER'], errors='coerce').astype('Int64')
    df_data['time'] = pd.to_datetime(df_data['time'], errors='coerce', utc=True)
    df_data['latitude'] = pd.to_numeric(df_data['latitude'], errors='coerce')
    df_data['longitude'] = pd.to_numeric(df_data['longitude'], errors='coerce')
    df_data['PRES_ADJUSTED'] = pd.to_numeric(df_data['PRES_ADJUSTED'], errors='coerce')
    df_data['PRES_ADJUSTED_QC'] = pd.to_numeric(df_data['PRES_ADJUSTED_QC'], errors='coerce').astype('Int64')
    df_data['TEMP_ADJUSTED'] = pd.to_numeric(df_data['TEMP_ADJUSTED'], errors='coerce')
    df_data['TEMP_ADJUSTED_QC'] = pd.to_numeric(df_data['TEMP_ADJUSTED_QC'], errors='coerce').astype('Int64')
    df_data['PSAL_ADJUSTED'] = pd.to_numeric(df_data['PSAL_ADJUSTED'], errors='coerce')
    df_data['PSAL_ADJUSTED_QC'] = pd.to_numeric(df_data['PSAL_ADJUSTED_QC'], errors='coerce').astype('Int64')

    # 4. Check Missing Required Fields
    req_cols = ['time', 'latitude', 'longitude', 'PRES_ADJUSTED', 'TEMP_ADJUSTED', 'PSAL_ADJUSTED']
    missing_mask = df_data[req_cols].isnull().any(axis=1)
    missing_rows_count = missing_mask.sum()
    print(f"\n3. Missing values check:")
    print(f"   Rows missing required fields ({', '.join(req_cols)}): {missing_rows_count}")

    df_valid = df_data[~missing_mask].copy()

    # 5. QC Filtering (KEEP QC in [1, 2], REMOVE QC == 3)
    qc_3_pres = (df_valid['PRES_ADJUSTED_QC'] == 3).sum()
    qc_3_temp = (df_valid['TEMP_ADJUSTED_QC'] == 3).sum()
    qc_3_psal = (df_valid['PSAL_ADJUSTED_QC'] == 3).sum()
    qc_3_any_mask = (df_valid['PRES_ADJUSTED_QC'] == 3) | (df_valid['TEMP_ADJUSTED_QC'] == 3) | (df_valid['PSAL_ADJUSTED_QC'] == 3)
    qc_3_total_removed = qc_3_any_mask.sum()

    print(f"\n4. QC Filtering (removing bad data QC=3):")
    print(f"   PRES_ADJUSTED_QC = 3: {qc_3_pres}")
    print(f"   TEMP_ADJUSTED_QC = 3: {qc_3_temp}")
    print(f"   PSAL_ADJUSTED_QC = 3: {qc_3_psal}")
    print(f"   Total unique rows removed by QC=3 filter: {qc_3_total_removed}")

    df_qc_filtered = df_valid[~qc_3_any_mask].copy()

    # Check for non-standard QC values (<1 or >3 or null)
    valid_qc_flags = [1, 2, 3]
    unexpected_qc = ~df_qc_filtered[['PRES_ADJUSTED_QC', 'TEMP_ADJUSTED_QC', 'PSAL_ADJUSTED_QC']].isin(valid_qc_flags).all(axis=1)
    unexpected_qc_count = unexpected_qc.sum()
    if unexpected_qc_count > 0:
        print(f"   WARNING: Found {unexpected_qc_count} rows with non-standard QC flags!")
    else:
        print("   All remaining rows have valid QC flags in {1, 2}.")

    # 6. Physical Validity Range Filters
    invalid_pres = (df_qc_filtered['PRES_ADJUSTED'] < 0.0) | (df_qc_filtered['PRES_ADJUSTED'] > 12000.0)
    invalid_temp = (df_qc_filtered['TEMP_ADJUSTED'] < -2.5) | (df_qc_filtered['TEMP_ADJUSTED'] > 40.0)
    invalid_psal = (df_qc_filtered['PSAL_ADJUSTED'] < 2.0) | (df_qc_filtered['PSAL_ADJUSTED'] > 41.0)
    invalid_lat = (df_qc_filtered['latitude'] < -90.0) | (df_qc_filtered['latitude'] > 90.0)
    invalid_lon = (df_qc_filtered['longitude'] < -180.0) | (df_qc_filtered['longitude'] > 180.0)

    print(f"\n5. Physical validity range checks:")
    print(f"   Pressure outside [0, 12000 dbar]:  {invalid_pres.sum()}")
    print(f"   Temperature outside [-2.5, 40 °C]: {invalid_temp.sum()}")
    print(f"   Salinity outside [2, 41 PSU]:      {invalid_psal.sum()}")
    print(f"   Latitude outside [-90, 90 °N]:     {invalid_lat.sum()}")
    print(f"   Longitude outside [-180, 180 °E]:  {invalid_lon.sum()}")

    phys_invalid_mask = invalid_pres | invalid_temp | invalid_psal | invalid_lat | invalid_lon
    df_clean = df_qc_filtered[~phys_invalid_mask].copy()

    # 7. Calculate Approximate Depth in Meters (UNESCO 1983 / Saunders & Fofonoff 1981)
    print("\n6. Calculating approximate depth (depth_m) via UNESCO (1983) formula...")
    depth_vals = pressure_to_depth_unesco1983(
        pressure_dbar=df_clean['PRES_ADJUSTED'].values,
        latitude_deg=df_clean['latitude'].values
    )
    df_clean['depth_m'] = np.round(depth_vals, 4)

    # 8. Select and Order Final Columns
    keep_cols = [
        'PLATFORM_NUMBER', 'CYCLE_NUMBER', 'time', 'latitude', 'longitude',
        'PRES_ADJUSTED', 'PRES_ADJUSTED_QC', 'TEMP_ADJUSTED', 'TEMP_ADJUSTED_QC',
        'PSAL_ADJUSTED', 'PSAL_ADJUSTED_QC', 'depth_m'
    ]
    df_final = df_clean[keep_cols].copy()
    df_final['time'] = df_final['time'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    # Save Output CSV
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df_final.to_csv(output_csv, index=False)
    print(f"\nSaved cleaned dataset to: {output_csv}")
    print(f"Final dataset shape:        {df_final.shape}")

    # 9. Automated Validation Checks
    print("\n==================================================================")
    print("Automated Post-Cleaning Validation Checks")
    print("==================================================================")
    temp_valid = (df_final['TEMP_ADJUSTED'].min() >= -2.5) and (df_final['TEMP_ADJUSTED'].max() <= 40.0)
    psal_valid = (df_final['PSAL_ADJUSTED'].min() >= 2.0) and (df_final['PSAL_ADJUSTED'].max() <= 41.0)
    pres_valid = (df_final['PRES_ADJUSTED'].min() >= 0.0) and (df_final['PRES_ADJUSTED'].max() <= 12000.0)
    lat_valid = (df_final['latitude'].min() >= -90.0) and (df_final['latitude'].max() <= 90.0)
    lon_valid = (df_final['longitude'].min() >= -180.0) and (df_final['longitude'].max() <= 180.0)
    no_missing = df_final[['time', 'latitude', 'longitude', 'PRES_ADJUSTED', 'TEMP_ADJUSTED', 'PSAL_ADJUSTED']].isnull().sum().sum() == 0
    no_qc_3 = (df_final['PRES_ADJUSTED_QC'] == 3).sum() == 0 and (df_final['TEMP_ADJUSTED_QC'] == 3).sum() == 0 and (df_final['PSAL_ADJUSTED_QC'] == 3).sum() == 0
    depth_valid = (df_final['depth_m'].min() >= 0.0) and np.issubdtype(df_final['depth_m'].dtype, np.number)

    print(f"Temperature check [-2.5, 40 °C]:   {'PASS' if temp_valid else 'FAIL'}")
    print(f"Salinity check [2, 41 PSU]:        {'PASS' if psal_valid else 'FAIL'}")
    print(f"Pressure check [0, 12000 dbar]:    {'PASS' if pres_valid else 'FAIL'}")
    print(f"Latitude check [-90, 90 °N]:       {'PASS' if lat_valid else 'FAIL'}")
    print(f"Longitude check [-180, 180 °E]:    {'PASS' if lon_valid else 'FAIL'}")
    print(f"No missing required fields:       {'PASS' if no_missing else 'FAIL'}")
    print(f"No QC=3 flags in final dataset:   {'PASS' if no_qc_3 else 'FAIL'}")
    print(f"Valid depth_m >= 0:               {'PASS' if depth_valid else 'FAIL'}")

    all_pass = all([temp_valid, psal_valid, pres_valid, lat_valid, lon_valid, no_missing, no_qc_3, depth_valid])
    print(f"\nOVERALL VALIDATION STATUS: {'PASS' if all_pass else 'FAIL'}")
    print("==================================================================\n")

    return df_final, all_pass


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    input_file = os.path.join(base_dir, "data/argo/Indian_ARGO_Floats_fba1_2d9b_5c9d.csv")
    output_file = os.path.join(base_dir, "data/argo/ARGO_OceanTwin_clean.csv")

    _, pass_status = clean_argo_dataset(input_file, output_file)
    if not pass_status:
        sys.exit(1)
