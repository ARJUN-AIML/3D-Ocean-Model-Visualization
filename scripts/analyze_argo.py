"""
Analyze Argo profiles from ArgoVis API for HYCOM matching.
Fetches real profiles, analyzes coverage, and generates a report.
Does NOT modify any backend code or train ML models.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta

OUTPUT_DIR = "docs/data-validation/real-hycom"
ARGO_CACHE = os.path.join(OUTPUT_DIR, "argo_profiles_raw.json")

# HYCOM coverage
HYCOM = {
    "time_start": "2026-08-30T06:00:00Z",
    "time_end":   "2026-09-06T00:00:00Z",
    "lat_min": -44.93, "lat_max": 30.95,
    "lon_min": 20.0,   "lon_max": 119.84,
    "depths": [0, 10, 50, 100, 250, 500],
}

# Alignment tolerances (from alignment.py)
TOLERANCES = {
    "max_spatial_distance_km": 200.0,
    "max_time_difference_hours": 48.0,
    "max_depth_difference_m": 100.0,
}


def fetch_argo_data():
    """Fetch Argo profiles from ArgoVis API with tolerance-extended window."""
    # Extend time window by tolerance
    start = "2026-08-28T00:00:00Z"
    end = "2026-09-08T00:00:00Z"
    
    all_profiles = []
    
    # Split into smaller longitude chunks to avoid 16MB API limit
    lon_chunks = [
        (20, 60), (60, 90), (90, 120)
    ]
    
    for lon_start, lon_end in lon_chunks:
        url = (
            f"https://argovis-api.colorado.edu/argo"
            f"?startDate={start}&endDate={end}"
            f"&box=[[{lon_start},{HYCOM['lat_min']}],[{lon_end},{HYCOM['lat_max']}]]"
            f"&data=temperature,salinity"
            f"&presRange=0,600"
        )
        print(f"  Fetching lon {lon_start}-{lon_end}...")
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=60) as response:
                text = response.read().decode("utf-8")
                # Parse JSON array
                if text.strip().startswith("["):
                    chunk = json.loads(text)
                    print(f"    Got {len(chunk)} profiles")
                    all_profiles.extend(chunk)
                else:
                    print(f"    Unexpected response format")
        except Exception as e:
            print(f"    Error: {e}")
    
    print(f"\nTotal profiles fetched: {len(all_profiles)}")
    return all_profiles


def analyze_profiles(profiles):
    """Analyze Argo profiles for HYCOM matching."""
    
    results = {
        "total_profiles": len(profiles),
        "unique_floats": set(),
        "dac_sources": set(),
        "time_distribution": {},
        "lat_distribution": [],
        "lon_distribution": [],
        "depth_range": {"min": float("inf"), "max": 0},
        "profiles_with_temp": 0,
        "profiles_with_sal": 0,
        "qc_stats": {"geolocation_qc_1": 0, "timestamp_qc_1": 0},
        "data_modes": {},
        "total_temp_measurements": 0,
        "total_sal_measurements": 0,
        "profiles_in_hycom_time": 0,
        "potential_match_points": 0,
        "profiles_detail": [],
    }
    
    for p in profiles:
        pid = p.get("_id", "unknown")
        float_id = pid.split("_")[0] if "_" in pid else pid
        results["unique_floats"].add(float_id)
        
        # Location
        coords = p.get("geolocation", {}).get("coordinates", [0, 0])
        lon, lat = coords[0], coords[1]
        results["lat_distribution"].append(lat)
        results["lon_distribution"].append(lon)
        
        # Time
        ts = p.get("timestamp", "")
        if ts:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            day_key = dt.strftime("%Y-%m-%d")
            results["time_distribution"][day_key] = results["time_distribution"].get(day_key, 0) + 1
            
            # Check if within HYCOM time window
            hycom_start = datetime.fromisoformat(HYCOM["time_start"].replace("Z", "+00:00"))
            hycom_end = datetime.fromisoformat(HYCOM["time_end"].replace("Z", "+00:00"))
            if hycom_start <= dt <= hycom_end:
                results["profiles_in_hycom_time"] += 1
        
        # QC
        if p.get("geolocation_argoqc") == 1:
            results["qc_stats"]["geolocation_qc_1"] += 1
        if p.get("timestamp_argoqc") == 1:
            results["qc_stats"]["timestamp_qc_1"] += 1
        
        # Source/DAC
        sources = p.get("source", [])
        for s in sources:
            url = s.get("url", "")
            if "dac/" in url:
                dac = url.split("dac/")[1].split("/")[0]
                results["dac_sources"].add(dac)
        
        # Data info
        data_info = p.get("data_info", [[], [], []])
        var_names = data_info[0] if len(data_info) > 0 else []
        mode_info = data_info[2] if len(data_info) > 2 else []
        
        has_temp = "temperature" in var_names
        has_sal = "salinity" in var_names
        has_pres = "pressure" in var_names
        
        if has_temp:
            results["profiles_with_temp"] += 1
        if has_sal:
            results["profiles_with_sal"] += 1
        
        # Data modes
        for i, var in enumerate(var_names):
            if i < len(mode_info):
                mode = mode_info[i][1] if len(mode_info[i]) > 1 else "?"
                results["data_modes"][mode] = results["data_modes"].get(mode, 0) + 1
        
        # Data arrays
        data = p.get("data", [])
        temp_idx = var_names.index("temperature") if "temperature" in var_names else -1
        sal_idx = var_names.index("salinity") if "salinity" in var_names else -1
        pres_idx = var_names.index("pressure") if "pressure" in var_names else -1
        
        n_levels = 0
        if temp_idx >= 0 and temp_idx < len(data):
            n_temp = len(data[temp_idx])
            results["total_temp_measurements"] += n_temp
            n_levels = n_temp
        if sal_idx >= 0 and sal_idx < len(data):
            results["total_sal_measurements"] += len(data[sal_idx])
        
        # Depth range from pressure
        if pres_idx >= 0 and pres_idx < len(data):
            pressures = data[pres_idx]
            if pressures:
                p_min = min(pressures)
                p_max = max(pressures)
                results["depth_range"]["min"] = min(results["depth_range"]["min"], p_min)
                results["depth_range"]["max"] = max(results["depth_range"]["max"], p_max)
                
                # Count potential match points (measurements within HYCOM depth range + tolerance)
                for pres in pressures:
                    for hd in HYCOM["depths"]:
                        if abs(pres - hd) <= TOLERANCES["max_depth_difference_m"]:
                            results["potential_match_points"] += 1
                            break
        
        # Profile detail
        results["profiles_detail"].append({
            "id": pid,
            "float": float_id,
            "lat": lat,
            "lon": lon,
            "time": ts,
            "n_levels": n_levels,
            "has_temp": has_temp,
            "has_sal": has_sal,
        })
    
    # Convert sets to lists for JSON
    results["unique_floats"] = sorted(list(results["unique_floats"]))
    results["dac_sources"] = sorted(list(results["dac_sources"]))
    
    return results


def check_sampling_bias(results):
    """Check for geographic, temporal, and depth bias."""
    bias = {}
    
    # Geographic clustering
    import statistics
    lats = results["lat_distribution"]
    lons = results["lon_distribution"]
    
    if lats:
        lat_mean = statistics.mean(lats)
        lat_std = statistics.stdev(lats) if len(lats) > 1 else 0
        lon_mean = statistics.mean(lons)
        lon_std = statistics.stdev(lons) if len(lons) > 1 else 0
        
        # Count by ocean basin/region  
        regions = {
            "Arabian Sea (50-78E, 0-30N)": 0,
            "Bay of Bengal (78-100E, 0-25N)": 0,
            "Equatorial IO (40-100E, 10S-10N)": 0,
            "Southern IO (20-120E, 45S-10S)": 0,
            "Eastern IO coast (90-120E, 25S-10N)": 0,
        }
        
        for lat, lon in zip(lats, lons):
            if 50 <= lon <= 78 and 0 <= lat <= 30:
                regions["Arabian Sea (50-78E, 0-30N)"] += 1
            if 78 <= lon <= 100 and 0 <= lat <= 25:
                regions["Bay of Bengal (78-100E, 0-25N)"] += 1
            if 40 <= lon <= 100 and -10 <= lat <= 10:
                regions["Equatorial IO (40-100E, 10S-10N)"] += 1
            if 20 <= lon <= 120 and -45 <= lat <= -10:
                regions["Southern IO (20-120E, 45S-10S)"] += 1
            if 90 <= lon <= 120 and -25 <= lat <= 10:
                regions["Eastern IO coast (90-120E, 25S-10N)"] += 1
        
        bias["geographic"] = {
            "lat_mean": round(lat_mean, 2),
            "lat_std": round(lat_std, 2),
            "lon_mean": round(lon_mean, 2),
            "lon_std": round(lon_std, 2),
            "regions": regions,
        }
    
    # Temporal clustering
    time_dist = results["time_distribution"]
    if time_dist:
        max_day = max(time_dist, key=time_dist.get)
        min_day = min(time_dist, key=time_dist.get)
        bias["temporal"] = {
            "days_with_profiles": len(time_dist),
            "max_profiles_day": f"{max_day}: {time_dist[max_day]}",
            "min_profiles_day": f"{min_day}: {time_dist[min_day]}",
            "profiles_per_day": {k: v for k, v in sorted(time_dist.items())},
        }
    
    # Float concentration
    float_counts = {}
    for p in results["profiles_detail"]:
        fid = p["float"]
        float_counts[fid] = float_counts.get(fid, 0) + 1
    max_float = max(float_counts, key=float_counts.get) if float_counts else "N/A"
    
    bias["float_diversity"] = {
        "total_unique_floats": len(results["unique_floats"]),
        "most_prolific_float": f"{max_float} ({float_counts.get(max_float, 0)} profiles)",
        "floats_with_multiple_profiles": sum(1 for v in float_counts.values() if v > 1),
    }
    
    return bias


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("=" * 70)
    print("ARGO PROFILE ANALYSIS FOR HYCOM MATCHING")
    print("=" * 70)
    
    # Fetch or load cached data
    if os.path.exists(ARGO_CACHE):
        print("\nLoading cached Argo data...")
        with open(ARGO_CACHE, "r") as f:
            profiles = json.load(f)
        print(f"  Loaded {len(profiles)} cached profiles")
    else:
        print("\nFetching Argo data from ArgoVis API...")
        profiles = fetch_argo_data()
        
        # Cache the raw data
        with open(ARGO_CACHE, "w") as f:
            json.dump(profiles, f)
        print(f"  Cached {len(profiles)} profiles to {ARGO_CACHE}")
    
    # Analyze
    print("\nAnalyzing profiles...")
    results = analyze_profiles(profiles)
    
    print(f"\n  Total profiles:           {results['total_profiles']}")
    print(f"  Unique floats:            {len(results['unique_floats'])}")
    print(f"  Profiles with temp:       {results['profiles_with_temp']}")
    print(f"  Profiles with salinity:   {results['profiles_with_sal']}")
    print(f"  Total temp measurements:  {results['total_temp_measurements']}")
    print(f"  Total sal measurements:   {results['total_sal_measurements']}")
    print(f"  Profiles in HYCOM time:   {results['profiles_in_hycom_time']}")
    print(f"  Potential match points:   {results['potential_match_points']}")
    print(f"  Depth range:              {results['depth_range']}")
    print(f"  DAC sources:              {results['dac_sources']}")
    print(f"  Data modes:               {results['data_modes']}")
    print(f"  QC stats:                 {results['qc_stats']}")
    
    # Time distribution
    print(f"\n  Time distribution:")
    for day, count in sorted(results["time_distribution"].items()):
        marker = " ← HYCOM" if "2026-08-30" <= day <= "2026-09-06" else ""
        print(f"    {day}: {count} profiles{marker}")
    
    # Sampling bias
    print("\nChecking sampling bias...")
    bias = check_sampling_bias(results)
    
    print(f"\n  Geographic spread:")
    print(f"    Lat: mean={bias['geographic']['lat_mean']}, std={bias['geographic']['lat_std']}")
    print(f"    Lon: mean={bias['geographic']['lon_mean']}, std={bias['geographic']['lon_std']}")
    print(f"  Regions:")
    for region, count in bias["geographic"]["regions"].items():
        print(f"    {region}: {count}")
    
    print(f"\n  Temporal spread:")
    print(f"    Days with profiles: {bias['temporal']['days_with_profiles']}")
    for day, count in bias["temporal"]["profiles_per_day"].items():
        print(f"    {day}: {count}")
    
    print(f"\n  Float diversity:")
    for k, v in bias["float_diversity"].items():
        print(f"    {k}: {v}")
    
    # Save analysis
    analysis = {
        "hycom_coverage": HYCOM,
        "alignment_tolerances": TOLERANCES,
        "argo_source": "ArgoVis API (https://argovis-api.colorado.edu)",
        "fetch_time_window": "2026-08-28 to 2026-09-08 (±2 days from HYCOM)",
        "fetch_spatial_window": f"Lon {HYCOM['lon_min']}-{HYCOM['lon_max']}, Lat {HYCOM['lat_min']}-{HYCOM['lat_max']}",
        "summary": {
            "total_profiles": results["total_profiles"],
            "unique_floats": len(results["unique_floats"]),
            "float_ids": results["unique_floats"],
            "profiles_with_temperature": results["profiles_with_temp"],
            "profiles_with_salinity": results["profiles_with_sal"],
            "total_temp_measurements": results["total_temp_measurements"],
            "total_sal_measurements": results["total_sal_measurements"],
            "profiles_in_hycom_time_window": results["profiles_in_hycom_time"],
            "potential_match_points": results["potential_match_points"],
            "depth_range_dbar": results["depth_range"],
            "dac_sources": results["dac_sources"],
            "data_modes": results["data_modes"],
            "qc_stats": results["qc_stats"],
        },
        "time_distribution": results["time_distribution"],
        "sampling_bias": bias,
        "profiles": results["profiles_detail"],
    }
    
    out_path = os.path.join(OUTPUT_DIR, "argo_analysis.json")
    with open(out_path, "w") as f:
        json.dump(analysis, f, indent=2, default=str)
    print(f"\n✅ Analysis saved to {out_path}")
    
    print("\n✅ No backend files modified.")
    print("✅ No ML training performed.")
    print("✅ No synthetic data generated.")


if __name__ == "__main__":
    main()
