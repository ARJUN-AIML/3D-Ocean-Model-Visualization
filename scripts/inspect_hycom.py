"""
Lightweight HYCOM Dataset Inspector.
Opens the 9 GB file lazily via xarray (NO .load(), NO full .values on data vars).
Inspects metadata, coordinates, variables, and performs small targeted data reads.
"""

import os
import sys
import time
import json
import struct
import numpy as np
import pandas as pd
import xarray as xr

# ─── CONFIG ──────────────────────────────────────────────────────────────
FILE_PATH = "data/hycom/RSMC_hycom_20260831.nc"
OUTPUT_DIR = "docs/data-validation/real-hycom"

def main():
    results = {}

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION A — FILE VERIFICATION
    # ═══════════════════════════════════════════════════════════════════════
    print("=" * 70)
    print("SECTION A: FILE VERIFICATION")
    print("=" * 70)

    if not os.path.exists(FILE_PATH):
        print(f"FATAL: File not found: {FILE_PATH}")
        sys.exit(1)

    file_size = os.path.getsize(FILE_PATH)
    file_size_gb = file_size / (1024 ** 3)
    print(f"  File exists:    YES")
    print(f"  Path:           {os.path.abspath(FILE_PATH)}")
    print(f"  Size (bytes):   {file_size:,}")
    print(f"  Size (GB):      {file_size_gb:.3f}")

    # Check magic bytes for NetCDF format
    with open(FILE_PATH, "rb") as f:
        magic = f.read(8)

    if magic[:3] == b'CDF':
        fmt = "NetCDF Classic (CDF)"
    elif magic[:4] == b'\x89HDF':
        fmt = "NetCDF-4 / HDF5"
    else:
        fmt = f"Unknown (magic: {magic[:4].hex()})"
    print(f"  Format:         {fmt}")

    # Simple corruption check: file > 1 GB and is NetCDF
    is_valid_format = "NetCDF" in fmt or "HDF" in fmt
    file_appears_complete = file_size > 1_000_000_000 and is_valid_format
    print(f"  Valid format:   {is_valid_format}")
    print(f"  Appears complete: {file_appears_complete} (size > 1GB and valid format)")

    results["file_verification"] = {
        "exists": True,
        "size_bytes": file_size,
        "size_gb": round(file_size_gb, 3),
        "format": fmt,
        "valid_format": is_valid_format,
        "appears_complete": file_appears_complete,
    }

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION B+C+D+E — LAZY DATASET OPEN + DIMENSIONS
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("SECTION B: OPENING DATASET LAZILY")
    print("=" * 70)

    t0 = time.perf_counter()
    try:
        ds = xr.open_dataset(FILE_PATH)
        t_open = time.perf_counter() - t0
        print(f"  Open SUCCESS in {t_open:.3f} seconds")
        print(f"  Engine used:    default (netcdf4)")
    except Exception as e:
        print(f"  Open FAILED: {e}")
        sys.exit(1)

    # Print basic structure manually (avoid repr which can trigger dask version bugs)
    print(f"\n  Dimensions:     {dict(ds.sizes)}")
    print(f"  Coordinates:    {list(ds.coords)}")
    print(f"  Data variables: {list(ds.data_vars)}")
    print(f"  Attrs:          {dict(ds.attrs)}\n")

    # DIMENSIONS
    print("=" * 70)
    print("SECTION B: DIMENSIONS")
    print("=" * 70)
    dims_info = {}
    for dim_name, dim_size in ds.sizes.items():
        dims_info[dim_name] = int(dim_size)
        print(f"  {dim_name}: {dim_size}")

    results["dimensions"] = dims_info

    # TIME
    print("\n" + "=" * 70)
    print("SECTION C: TIME COVERAGE")
    print("=" * 70)
    time_info = {}
    if "TIME" in ds.coords:
        time_vals = ds["TIME"].values
        time_size = len(time_vals)
        # Decode time: units = "days since 1900-12-31"
        time_units = ds["TIME"].attrs.get("units", "unknown")
        time_calendar = ds["TIME"].attrs.get("calendar", "unknown")

        # Try to decode to datetime
        try:
            time_decoded = pd.to_datetime(
                ds["TIME"].values,
                origin=pd.Timestamp("1900-12-31"),
                unit="D"
            ) if "days since" in time_units else pd.to_datetime(ds["TIME"].values)
        except:
            time_decoded = None

        # If xarray already decoded the time
        if np.issubdtype(ds["TIME"].dtype, np.datetime64):
            time_decoded = pd.DatetimeIndex(ds["TIME"].values)
        elif time_decoded is None:
            # Manual decode
            raw_vals = ds["TIME"].values
            base = pd.Timestamp("1900-12-31")
            time_decoded = pd.DatetimeIndex([base + pd.Timedelta(days=float(v)) for v in raw_vals])

        first_time = str(time_decoded[0])
        last_time = str(time_decoded[-1])

        if time_size > 1:
            dt = time_decoded[1] - time_decoded[0]
            interval_hours = dt.total_seconds() / 3600
        else:
            interval_hours = None

        print(f"  Dimension name: TIME")
        print(f"  Size:           {time_size}")
        print(f"  Units:          {time_units}")
        print(f"  Calendar:       {time_calendar}")
        print(f"  First time:     {first_time}")
        print(f"  Last time:      {last_time}")
        print(f"  Interval:       {interval_hours} hours" if interval_hours else "  Interval: N/A")
        print(f"  dtype:          {ds['TIME'].dtype}")

        if time_decoded is not None and len(time_decoded) > 1:
            is_monotonic = time_decoded.is_monotonic_increasing
            print(f"  Monotonic:      {is_monotonic}")
        else:
            is_monotonic = True

        time_info = {
            "dim_name": "TIME",
            "size": time_size,
            "units": time_units,
            "calendar": time_calendar,
            "first": first_time,
            "last": last_time,
            "interval_hours": interval_hours,
            "monotonic": is_monotonic,
        }
    else:
        print("  TIME coordinate NOT found!")
        # Check alternative names
        for c in ds.coords:
            if "time" in str(c).lower():
                print(f"  Found alternative: {c}")

    results["time_coverage"] = time_info

    # DEPTH
    print("\n" + "=" * 70)
    print("SECTION D: DEPTH COVERAGE")
    print("=" * 70)
    depth_info = {}
    if "DEPTH" in ds.coords:
        depth_vals = ds["DEPTH"].values
        depth_attrs = dict(ds["DEPTH"].attrs)
        positive = depth_attrs.get("positive", "unknown")
        depth_units = depth_attrs.get("standard_name", "depth")

        print(f"  Dimension name: DEPTH")
        print(f"  Size:           {len(depth_vals)}")
        print(f"  Levels:         {depth_vals.tolist()}")
        print(f"  Min depth:      {float(np.min(depth_vals))}")
        print(f"  Max depth:      {float(np.max(depth_vals))}")
        print(f"  Positive:       {positive}")
        print(f"  dtype:          {ds['DEPTH'].dtype}")
        print(f"  Attributes:     {depth_attrs}")

        depth_info = {
            "dim_name": "DEPTH",
            "size": len(depth_vals),
            "levels": [float(v) for v in depth_vals],
            "min": float(np.min(depth_vals)),
            "max": float(np.max(depth_vals)),
            "positive": positive,
            "attrs": {k: str(v) for k, v in depth_attrs.items()},
        }
    else:
        print("  DEPTH coordinate NOT found!")

    results["depth_coverage"] = depth_info

    # LATITUDE
    print("\n" + "=" * 70)
    print("SECTION E: GEOGRAPHIC COVERAGE — LATITUDE")
    print("=" * 70)
    lat_info = {}
    if "LAT" in ds.coords:
        lat_vals = ds["LAT"].values
        lat_min = float(np.min(lat_vals))
        lat_max = float(np.max(lat_vals))
        lat_size = len(lat_vals)
        lat_spacing = ds["LAT"].attrs.get("point_spacing", "unknown")

        # Calculate actual spacing
        if lat_size > 1:
            diffs = np.diff(lat_vals)
            mean_spacing = float(np.mean(diffs))
            min_spacing = float(np.min(diffs))
            max_spacing = float(np.max(diffs))
            is_uniform = np.allclose(diffs, diffs[0], rtol=1e-4)
        else:
            mean_spacing = min_spacing = max_spacing = 0.0
            is_uniform = True

        print(f"  Dimension name: LAT")
        print(f"  Size:           {lat_size}")
        print(f"  Min:            {lat_min:.6f}")
        print(f"  Max:            {lat_max:.6f}")
        print(f"  Mean spacing:   {mean_spacing:.6f}°")
        print(f"  Min spacing:    {min_spacing:.6f}°")
        print(f"  Max spacing:    {max_spacing:.6f}°")
        print(f"  Uniform:        {is_uniform}")
        print(f"  Attr spacing:   {lat_spacing}")

        lat_info = {
            "dim_name": "LAT", "size": lat_size,
            "min": lat_min, "max": lat_max,
            "mean_spacing_deg": round(mean_spacing, 6),
            "min_spacing_deg": round(min_spacing, 6),
            "max_spacing_deg": round(max_spacing, 6),
            "uniform": is_uniform,
        }

    results["latitude"] = lat_info

    # LONGITUDE
    print("\n" + "=" * 70)
    print("SECTION E: GEOGRAPHIC COVERAGE — LONGITUDE")
    print("=" * 70)
    lon_info = {}
    if "LON" in ds.coords:
        lon_vals = ds["LON"].values
        lon_min = float(np.min(lon_vals))
        lon_max = float(np.max(lon_vals))
        lon_size = len(lon_vals)
        lon_spacing = ds["LON"].attrs.get("point_spacing", "unknown")

        if lon_size > 1:
            diffs = np.diff(lon_vals)
            mean_spacing = float(np.mean(diffs))
            is_uniform = np.allclose(diffs, diffs[0], rtol=1e-4)
        else:
            mean_spacing = 0.0
            is_uniform = True

        print(f"  Dimension name: LON")
        print(f"  Size:           {lon_size}")
        print(f"  Min:            {lon_min:.6f}")
        print(f"  Max:            {lon_max:.6f}")
        print(f"  Mean spacing:   {mean_spacing:.6f}°")
        print(f"  Uniform:        {is_uniform}")
        print(f"  Attr spacing:   {lon_spacing}")

        lon_info = {
            "dim_name": "LON", "size": lon_size,
            "min": lon_min, "max": lon_max,
            "mean_spacing_deg": round(mean_spacing, 6),
            "uniform": is_uniform,
        }

    results["longitude"] = lon_info

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION F — ALL VARIABLES
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("SECTION F: ALL VARIABLES")
    print("=" * 70)

    vars_info = {}
    for vname in ds.data_vars:
        da = ds[vname]
        attrs = dict(da.attrs)
        fill_val = attrs.get("_FillValue", attrs.get("missing_value", "N/A"))
        units = attrs.get("units", "not specified")
        long_name = attrs.get("long_name", vname)
        standard_name = attrs.get("standard_name", "N/A")
        dims_list = list(da.dims)

        encoding = da.encoding
        chunks = encoding.get("chunksizes", "not chunked")
        compression = encoding.get("zlib", False) or encoding.get("compression", "none")

        print(f"\n  Variable: {vname}")
        print(f"    Dimensions:   {dims_list}")
        print(f"    Shape:        {da.shape}")
        print(f"    dtype:        {da.dtype}")
        print(f"    Units:        {units}")
        print(f"    Long name:    {long_name}")
        print(f"    Std name:     {standard_name}")
        print(f"    FillValue:    {fill_val}")
        print(f"    Chunks:       {chunks}")
        print(f"    Compression:  {compression}")

        vars_info[str(vname)] = {
            "dimensions": dims_list,
            "shape": list(da.shape),
            "dtype": str(da.dtype),
            "units": str(units),
            "long_name": str(long_name),
            "standard_name": str(standard_name),
            "fill_value": str(fill_val),
            "chunking": str(chunks),
            "compression": str(compression),
        }

    results["variables"] = vars_info

    # Also list all coordinates that are not dims
    print("\n  --- Additional Coordinates ---")
    for cname in ds.coords:
        if cname not in ds.dims:
            print(f"  Coordinate (non-dim): {cname}, shape={ds[cname].shape}, dtype={ds[cname].dtype}")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION G — DATA QUALITY (small targeted reads only)
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("SECTION G: DATA QUALITY (targeted reads)")
    print("=" * 70)
    print("  Reading single time step surface slice for each 4D variable...")
    print("  This reads ~1/28th of depth=0 plane per variable (small fraction of 9 GB)")

    quality_info = {}
    for vname in ["TEMP", "SALN", "UVEL", "VVEL", "SSH", "MLD", "TCHP", "SALNA", "TEMP_CT"]:
        if vname not in ds.data_vars:
            print(f"\n  {vname}: NOT PRESENT")
            continue

        da = ds[vname]
        fill_val = da.attrs.get("_FillValue", da.attrs.get("missing_value", None))

        # Read only t=0, depth=0 (surface) slice if 4D, else t=0 if 3D
        try:
            t_start = time.perf_counter()
            if "DEPTH" in da.dims:
                # 4D: read first time, first depth
                sample = da.isel(TIME=0, DEPTH=0).values
            else:
                # 3D: read first time
                sample = da.isel(TIME=0).values
            t_read = time.perf_counter() - t_start

            # Count fill values and NaNs
            if fill_val is not None:
                fill_mask = (sample == fill_val)
                nan_mask = np.isnan(sample)
                missing_mask = fill_mask | nan_mask
            else:
                nan_mask = np.isnan(sample)
                missing_mask = nan_mask

            total_cells = sample.size
            missing_count = int(np.sum(missing_mask))
            missing_pct = (missing_count / total_cells) * 100

            # Stats on valid data
            valid = sample[~missing_mask]
            if len(valid) > 0:
                v_min = float(np.min(valid))
                v_max = float(np.max(valid))
                v_mean = float(np.mean(valid))
                v_std = float(np.std(valid))
            else:
                v_min = v_max = v_mean = v_std = float("nan")

            print(f"\n  {vname} (t=0, surface):")
            print(f"    Shape:        {sample.shape}")
            print(f"    Read time:    {t_read:.3f}s")
            print(f"    Total cells:  {total_cells:,}")
            print(f"    Missing:      {missing_count:,} ({missing_pct:.1f}%)")
            print(f"    Valid min:    {v_min:.4f}")
            print(f"    Valid max:    {v_max:.4f}")
            print(f"    Valid mean:   {v_mean:.4f}")
            print(f"    Valid std:    {v_std:.4f}")
            print(f"    FillValue:    {fill_val}")

            quality_info[vname] = {
                "sample_slice": "t=0, depth=0 (surface)" if "DEPTH" in da.dims else "t=0",
                "sample_shape": list(sample.shape),
                "read_time_sec": round(t_read, 3),
                "total_cells": total_cells,
                "missing_count": missing_count,
                "missing_pct": round(missing_pct, 2),
                "valid_min": round(v_min, 6) if not np.isnan(v_min) else "NaN",
                "valid_max": round(v_max, 6) if not np.isnan(v_max) else "NaN",
                "valid_mean": round(v_mean, 6) if not np.isnan(v_mean) else "NaN",
                "valid_std": round(v_std, 6) if not np.isnan(v_std) else "NaN",
                "fill_value": str(fill_val),
            }

        except Exception as e:
            print(f"\n  {vname}: READ ERROR — {e}")
            quality_info[vname] = {"error": str(e)}

    results["data_quality"] = quality_info

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION H — COMPATIBILITY CHECK
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("SECTION H: BACKEND COMPATIBILITY CHECK")
    print("=" * 70)

    # canonical.py VARIABLE_ALIASES
    VARIABLE_ALIASES = {
        "temp": "temperature", "t_an": "temperature", "votemper": "temperature", "thetao": "temperature",
        "sal": "salinity", "s_an": "salinity", "vosaline": "salinity", "so": "salinity",
        "u_current": "u", "u_vel": "u", "vozocrtx": "u", "uo": "u",
        "v_current": "v", "v_vel": "v", "vomecrty": "v", "vo": "v",
        "w_current": "w", "w_vel": "w", "vovecrtz": "w", "wo": "w",
        "chl": "chlorophyll", "chlor_a": "chlorophyll",
    }

    COORD_ALIASES = {
        "lat": "latitude", "lats": "latitude", "nav_lat": "latitude", "latitude": "latitude",
        "lon": "longitude", "long": "longitude", "lons": "longitude", "nav_lon": "longitude", "longitude": "longitude",
        "lev": "depth", "level": "depth", "depth_m": "depth", "z": "depth", "depth": "depth",
        "t": "time", "datetime": "time", "time": "time",
    }

    compat = {"coordinates": {}, "variables": {}, "issues": []}

    # Check coordinates
    for orig_coord in ds.coords:
        lower = str(orig_coord).lower()
        mapped = COORD_ALIASES.get(lower, None)
        status = "MAPPED" if mapped else "UNMAPPED"
        compat["coordinates"][str(orig_coord)] = {
            "lower": lower,
            "mapped_to": mapped,
            "status": status,
        }
        symbol = "✅" if mapped else "⚠️"
        print(f"  {symbol} Coord: {orig_coord} (lower: {lower}) → {mapped or 'NO MAPPING'}")

    # Check data variables
    for orig_var in ds.data_vars:
        lower = str(orig_var).lower()
        mapped = VARIABLE_ALIASES.get(lower, None)
        status = "MAPPED" if mapped else "UNMAPPED"
        compat["variables"][str(orig_var)] = {
            "lower": lower,
            "mapped_to": mapped,
            "status": status,
        }
        symbol = "✅" if mapped else "❌"
        print(f"  {symbol} Var:   {orig_var} (lower: {lower}) → {mapped or 'NO MAPPING'}")

    # Critical issues
    missing_aliases = []
    for vname in ["SALN", "UVEL", "VVEL"]:
        lower = vname.lower()
        if lower not in VARIABLE_ALIASES:
            missing_aliases.append(vname)
            compat["issues"].append(f"CRITICAL: Variable '{vname}' (lower: '{lower}') has no alias in canonical.py")

    if missing_aliases:
        print(f"\n  ⛔ MISSING ALIASES: {missing_aliases}")
        print("     These must be added to VARIABLE_ALIASES in canonical.py before pipeline use.")

    # DatasetManager path issue
    dm_issue = "DatasetManager.list_datasets() scans data/raw/*.* but file is in data/raw/model/. Subdirectory not scanned."
    compat["issues"].append(f"WARNING: {dm_issue}")
    print(f"\n  ⚠️  {dm_issue}")

    dm_issue2 = "DatasetManager.load_dataset() looks for data/raw/{id}.nc — will not find data/raw/model/{id}.nc"
    compat["issues"].append(f"WARNING: {dm_issue2}")
    print(f"  ⚠️  {dm_issue2}")

    # Validator memory issue
    val_issue = "validator.py does .values on full data variables (line 153/168) — would load 9GB into RAM on this dataset."
    compat["issues"].append(f"WARNING: {val_issue}")
    print(f"  ⚠️  {val_issue}")

    # Profiler memory issue
    prof_issue = "profiler.py does .values on every data variable (line 77) — would load 9GB into RAM."
    compat["issues"].append(f"WARNING: {prof_issue}")
    print(f"  ⚠️  {prof_issue}")

    results["compatibility"] = compat

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION I — DatasetManager TEST (metadata only)
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("SECTION I: DatasetManager TEST")
    print("=" * 70)

    dm_test = {}
    try:
        sys.path.insert(0, os.path.abspath("."))
        from backend.science.canonical import normalize_dataset_schema as normalize

        # Test normalization on the lazily-opened dataset
        t0 = time.perf_counter()
        ds_norm = normalize(ds)
        t_norm = time.perf_counter() - t0

        print(f"  normalize_dataset_schema: SUCCESS ({t_norm:.3f}s)")
        print(f"  Normalized coords: {list(ds_norm.coords)}")
        print(f"  Normalized vars:   {list(ds_norm.data_vars)}")

        # Check what got renamed
        renamed = {k: v for k, v in [
            ("LAT→latitude", "latitude" in ds_norm.coords),
            ("LON→longitude", "longitude" in ds_norm.coords),
            ("DEPTH→depth", "depth" in ds_norm.coords),
            ("TIME→time", "time" in ds_norm.coords),
            ("TEMP→temperature", "temperature" in ds_norm.data_vars),
            ("SALN→salinity", "salinity" in ds_norm.data_vars),
            ("UVEL→u", "u" in ds_norm.data_vars),
            ("VVEL→v", "v" in ds_norm.data_vars),
        ]}
        for mapping, success in renamed.items():
            symbol = "✅" if success else "❌"
            print(f"    {symbol} {mapping}: {success}")

        dm_test["normalize_success"] = True
        dm_test["normalize_time"] = round(t_norm, 3)
        dm_test["renamed"] = renamed

    except Exception as e:
        print(f"  normalize_dataset_schema: FAILED — {e}")
        dm_test["normalize_success"] = False
        dm_test["error"] = str(e)

    results["dataset_manager_test"] = dm_test

    # ═══════════════════════════════════════════════════════════════════════
    # SAVE RESULTS
    # ═══════════════════════════════════════════════════════════════════════
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # JSON profile
    json_path = os.path.join(OUTPUT_DIR, "hycom_profile.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✅ JSON profile saved to: {json_path}")

    # Close dataset
    ds.close()
    print("\n✅ Dataset closed. No full data was loaded into RAM.")
    print("✅ Original HYCOM file was NOT modified.")


if __name__ == "__main__":
    main()
