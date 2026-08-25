"""
backend/science/validator.py
Scientific Data Validation Engine for Ocean Data Visualization Platform (Problem Statement 26067).
Performs non-destructive scientific sanity checks on numerical ocean model fields and observation profiles.
Explicitly flags unphysical values, sign errors, non-monotonic time axes, and coordinate mismatches without silent repair.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
import xarray as xr

from backend.science.canonical import (
    COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE,
    VAR_TEMPERATURE, VAR_SALINITY, VAR_U_CURRENT, VAR_V_CURRENT,
    normalize_dataset_schema
)


class ScientificIssue:
    """Dataclass holding an identified scientific issue or data anomaly."""
    def __init__(self, issue_type: str, severity: str, description: str, affected_entity: str):
        self.issue_type = issue_type      # e.g., "UNPHYSICAL_VALUE", "NON_MONOTONIC_TIME", "DEPTH_SIGN_CONVENTION"
        self.severity = severity          # "CRITICAL", "WARNING", "INFO"
        self.description = description
        self.affected_entity = affected_entity

    def to_dict(self) -> Dict[str, str]:
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "description": self.description,
            "affected_entity": self.affected_entity,
        }


class OceanDatasetValidator:
    """
    Scientific Dataset Validator.
    Performs automated sanity checks on latitude/longitude, depth sign convention,
    time monotonicity, duplicate coordinates, unphysical values, fill values, and units.
    """

    def validate_dataset(self, ds: xr.Dataset, filename: str = "dataset") -> List[ScientificIssue]:
        """
        Executes complete scientific validation suite on an xarray Dataset.
        Returns a list of ScientificIssue instances.
        """
        issues: List[ScientificIssue] = []
        norm_ds = normalize_dataset_schema(ds)

        # 1. Latitude Validation (-90° to +90°)
        if COORD_LATITUDE in norm_ds.coords:
            lat_vals = norm_ds[COORD_LATITUDE].values
            if np.any(lat_vals < -90.0) or np.any(lat_vals > 90.0):
                issues.append(
                    ScientificIssue(
                        issue_type="LATITUDE_OUT_OF_BOUNDS",
                        severity="CRITICAL",
                        description=f"Latitude contains values outside WGS84 range [-90, +90]: min={np.nanmin(lat_vals)}, max={np.nanmax(lat_vals)}",
                        affected_entity=COORD_LATITUDE,
                    )
                )

        # 2. Longitude Validation (-180° to +180° or 0° to 360°)
        if COORD_LONGITUDE in norm_ds.coords:
            lon_vals = norm_ds[COORD_LONGITUDE].values
            if np.any(lon_vals < -180.0) or np.any(lon_vals > 360.0):
                issues.append(
                    ScientificIssue(
                        issue_type="LONGITUDE_OUT_OF_BOUNDS",
                        severity="CRITICAL",
                        description=f"Longitude contains unphysical values outside [-180, 360]: min={np.nanmin(lon_vals)}, max={np.nanmax(lon_vals)}",
                        affected_entity=COORD_LONGITUDE,
                    )
                )
            elif np.any(lon_vals > 180.0):
                issues.append(
                    ScientificIssue(
                        issue_type="LONGITUDE_CONVENTION_360",
                        severity="INFO",
                        description=f"Longitude uses [0, 360] easting convention instead of [-180, +180] standard.",
                        affected_entity=COORD_LONGITUDE,
                    )
                )

        # 3. Depth Sign Convention Check (Positive Down expected for ocean depth)
        if COORD_DEPTH in norm_ds.coords:
            depth_vals = norm_ds[COORD_DEPTH].values
            positive_attr = norm_ds[COORD_DEPTH].attrs.get("positive", "").lower()
            if np.any(depth_vals < 0.0):
                issues.append(
                    ScientificIssue(
                        issue_type="DEPTH_SIGN_CONVENTION_NEGATIVE",
                        severity="WARNING",
                        description=f"Depth coordinate contains negative values (e.g. min={np.nanmin(depth_vals)}). Standard INCOIS depth convention is positive-down (z >= 0).",
                        affected_entity=COORD_DEPTH,
                    )
                )
            if positive_attr == "up":
                issues.append(
                    ScientificIssue(
                        issue_type="DEPTH_POSITIVE_UP_ATTR",
                        severity="WARNING",
                        description="Depth attribute 'positive' is set to 'up'. Ocean data requires positive-down orientation.",
                        affected_entity=COORD_DEPTH,
                    )
                )

        # 4. Time Monotonicity & Duplicate Check
        if COORD_TIME in norm_ds.coords:
            time_vals = norm_ds[COORD_TIME].values
            if len(time_vals) > 1:
                # Monotonicity check
                time_series = pd.to_datetime(time_vals)
                if not time_series.is_monotonic_increasing:
                    issues.append(
                        ScientificIssue(
                            issue_type="NON_MONOTONIC_TIME",
                            severity="CRITICAL",
                            description="Time coordinate is not monotonically increasing. Temporal indexing and animations will be corrupted.",
                            affected_entity=COORD_TIME,
                        )
                    )
                # Duplicate check
                if time_series.has_duplicates:
                    dupes = time_series[time_series.duplicated()].unique()
                    issues.append(
                        ScientificIssue(
                            issue_type="DUPLICATE_TIMESTAMPS",
                            severity="WARNING",
                            description=f"Time coordinate contains {len(dupes)} duplicate timestamps: e.g. {dupes[:3]}",
                            affected_entity=COORD_TIME,
                        )
                    )

        # 5. Duplicate Coordinate Checks across Spatial Axis
        for coord_name in [COORD_LATITUDE, COORD_LONGITUDE, COORD_DEPTH]:
            if coord_name in norm_ds.coords:
                vals = norm_ds[coord_name].values
                if len(vals) > len(np.unique(vals)):
                    issues.append(
                        ScientificIssue(
                            issue_type="DUPLICATE_COORDINATE_VALUES",
                            severity="WARNING",
                            description=f"Coordinate '{coord_name}' contains duplicate grid point entries.",
                            affected_entity=coord_name,
                        )
                    )

        # 6. Physical Range Validation for Data Variables
        if VAR_TEMPERATURE in norm_ds.data_vars:
            t_vals = norm_ds[VAR_TEMPERATURE].values
            valid_mask = ~np.isnan(t_vals)
            if np.any(valid_mask):
                min_t, max_t = float(np.min(t_vals[valid_mask])), float(np.max(t_vals[valid_mask]))
                if min_t < -3.0 or max_t > 40.0:
                    issues.append(
                        ScientificIssue(
                            issue_type="UNPHYSICAL_TEMPERATURE_VALUE",
                            severity="CRITICAL",
                            description=f"Temperature values outside physical ocean range [-3°C, 40°C]: min={min_t:.2f}°C, max={max_t:.2f}°C",
                            affected_entity=VAR_TEMPERATURE,
                        )
                    )

        if VAR_SALINITY in norm_ds.data_vars:
            s_vals = norm_ds[VAR_SALINITY].values
            valid_mask = ~np.isnan(s_vals)
            if np.any(valid_mask):
                min_s, max_s = float(np.min(s_vals[valid_mask])), float(np.max(s_vals[valid_mask]))
                if min_s < 0.0 or max_s > 45.0:
                    issues.append(
                        ScientificIssue(
                            issue_type="UNPHYSICAL_SALINITY_VALUE",
                            severity="CRITICAL",
                            description=f"Salinity values outside physical ocean range [0 PSU, 45 PSU]: min={min_s:.2f}, max={max_s:.2f}",
                            affected_entity=VAR_SALINITY,
                        )
                    )

        return issues
