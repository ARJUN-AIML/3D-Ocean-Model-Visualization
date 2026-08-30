"""
backend/science/alignment_report.py
Model-vs-Observation Alignment Performance Reporting Engine.
Generates structured machine-readable (dict/JSON) and human-readable Markdown reports detailing:
- Total observations processed, valid, rejected, matched, unmatched, and match percentage.
- Mean spatial distance (km), mean depth difference (m), and mean time difference (hours).
- Variable pair counts (Temperature, Salinity, Velocity).
- Detailed breakdown of rejection and match failure causes.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from backend.ml.schemas import ObservationRecord
from backend.ml.preprocessing.alignment import ModelObservationAligner


def generate_alignment_report(
    df_aligned: pd.DataFrame,
    total_observations_input: int,
    rejected_qc_count: int = 0,
    target_variable: str = "temperature",
    dataset_id: str = "model_dataset",
) -> Dict[str, Any]:
    """
    Generates structured alignment metrics dictionary and markdown summary report.
    """
    matched_count = len(df_aligned)
    unmatched_count = max(0, total_observations_input - matched_count - rejected_qc_count)
    valid_input_count = max(0, total_observations_input - rejected_qc_count)

    match_pct = round((matched_count / valid_input_count * 100.0), 2) if valid_input_count > 0 else 0.0

    if not df_aligned.empty:
        mean_spatial_dist_km = round(float(df_aligned["spatial_distance_km"].mean()), 2)
        mean_depth_diff_m = round(float(df_aligned["depth_delta_m"].mean()), 2)
        mean_time_diff_h = round(float(df_aligned["time_delta_hours"].mean()), 2)

        temp_pairs = int(df_aligned["obs_temperature"].notna().sum()) if "obs_temperature" in df_aligned.columns else 0
        sal_pairs = int(df_aligned["obs_salinity"].notna().sum()) if "obs_salinity" in df_aligned.columns else 0
        u_pairs = int(df_aligned["model_u"].notna().sum()) if "model_u" in df_aligned.columns else 0

        mean_bias = round(float(df_aligned["bias"].mean()), 4) if "bias" in df_aligned.columns else 0.0
        abs_bias_std = round(float(df_aligned["bias"].std()), 4) if "bias" in df_aligned.columns else 0.0
    else:
        mean_spatial_dist_km = 0.0
        mean_depth_diff_m = 0.0
        mean_time_diff_h = 0.0
        temp_pairs = 0
        sal_pairs = 0
        u_pairs = 0
        mean_bias = 0.0
        abs_bias_std = 0.0

    report = {
        "dataset_id": dataset_id,
        "target_variable": target_variable,
        "summary": {
            "total_observations_input": total_observations_input,
            "valid_observations": valid_input_count,
            "rejected_qc_observations": rejected_qc_count,
            "matched_observations": matched_count,
            "unmatched_observations": unmatched_count,
            "match_percentage": match_pct,
        },
        "spatial_temporal_quality": {
            "mean_spatial_distance_km": mean_spatial_dist_km,
            "mean_depth_difference_m": mean_depth_diff_m,
            "mean_time_difference_hours": mean_time_diff_h,
        },
        "variable_pair_counts": {
            "temperature_pairs": temp_pairs,
            "salinity_pairs": sal_pairs,
            "velocity_pairs": u_pairs,
        },
        "raw_bias_statistics": {
            "mean_raw_bias": mean_bias,
            "std_raw_bias": abs_bias_std,
        },
        "markdown_report": f"""### Model-vs-Observation Alignment Summary
- **Dataset ID**: `{dataset_id}`
- **Target Variable**: `{target_variable}`
- **Total Observations Processed**: {total_observations_input}
- **Valid Observations**: {valid_input_count} (Rejected QC: {rejected_qc_count})
- **Matched Observations**: {matched_count} ({match_pct}% Match Rate)
- **Unmatched Observations**: {unmatched_count}
- **Mean Offsets**: Spatial: `{mean_spatial_dist_km} km` | Depth: `{mean_depth_diff_m} m` | Time: `{mean_time_diff_h} hrs`
- **Pairs Extracted**: Temp: {temp_pairs} | Sal: {sal_pairs} | Vel: {u_pairs}
- **Raw Model Bias (Obs - Model)**: `{mean_bias:.4f} ± {abs_bias_std:.4f}`
"""
    }
    return report
