"""
backend/api/services/anomaly_service.py
Service for calculating ocean temperature and salinity anomalies (ΔT, ΔS) and Z-scores
against historical monthly VAM climatology baseline.
"""

import logging
from typing import Dict, Any, Optional
from pandas import to_datetime

from backend.api.services.vam_baseline_service import VAMBaselineService

logger = logging.getLogger(__name__)


class AnomalyService:
    def __init__(self, vam_baseline_service: VAMBaselineService):
        self.baseline_service = vam_baseline_service

    def calculate_anomaly(
        self,
        variable: str,
        value: float,
        time: str,
        latitude: float,
        longitude: float,
        depth: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Calculate anomaly (Δ = value - baseline_mean) and Z-score ((value - mean) / std)
        for a given observation or prediction value at (time, lat, lon, depth).
        """
        # Parse month from input timestamp
        dt = to_datetime(time, utc=True)
        month = dt.month

        # Query historical 5-year VAM baseline mean and std
        baseline_res = self.baseline_service.get_baseline_point(
            variable=variable,
            month=month,
            latitude=latitude,
            longitude=longitude,
            depth=depth,
        )

        mean_val = baseline_res["baseline_mean"]
        std_val = baseline_res["baseline_std"]
        units = baseline_res["units"]
        raw_var = baseline_res["variable"]

        if mean_val is None:
            anomaly = None
            z_score = None
        else:
            anomaly = float(value - mean_val)
            if std_val is not None and std_val > 1e-6:
                z_score = float(anomaly / std_val)
            else:
                z_score = None

        return {
            "variable": raw_var,
            "units": units,
            "time": time,
            "latitude": latitude,
            "longitude": longitude,
            "depth": depth,
            "current_value": round(float(value), 4),
            "baseline_mean": round(mean_val, 4) if mean_val is not None else None,
            "baseline_std": round(std_val, 4) if std_val is not None else None,
            "anomaly": round(anomaly, 4) if anomaly is not None else None,
            "z_score": round(z_score, 4) if z_score is not None else None,
            "source_baseline": "INCOIS Monthly Gridded Argo VAM",
        }
