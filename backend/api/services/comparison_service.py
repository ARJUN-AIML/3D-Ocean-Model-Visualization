"""
backend/api/services/comparison_service.py
Service for matching and comparing HYCOM ocean model predictions against in-situ Argo observations.
"""

import math
import logging
from typing import Dict, Any, Optional
from pandas import to_datetime

from backend.api.services.hycom_service import HycomService
from backend.api.services.argo_service import ArgoService

logger = logging.getLogger(__name__)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two (lat, lon) points in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class ComparisonService:
    def __init__(self, hycom_service: HycomService, argo_service: ArgoService):
        self.hycom_service = hycom_service
        self.argo_service = argo_service

    def compare_point(
        self,
        platform_number: Optional[str] = None,
        cycle_number: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        depth: Optional[float] = None,
        time: Optional[str] = None,
        observed_temperature: Optional[float] = None,
        observed_salinity: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Compare an Argo observation against nearest HYCOM model prediction.
        If platform_number & cycle_number are provided, looks up real Argo observation first.
        """
        # If platform and cycle provided, fetch real observation from ArgoService
        if platform_number is not None and cycle_number is not None:
            profile = self.argo_service.get_profile(platform_number, cycle_number)
            plat_id = profile["platform_number"]
            cyc_id = profile["cycle_number"]
            obs_time = profile["time"]
            obs_lat = profile["latitude"]
            obs_lon = profile["longitude"]
            
            # Select target depth index (nearest to requested depth or surface depth)
            depths = profile["depths"]
            if depth is not None:
                idx = min(range(len(depths)), key=lambda i: abs(depths[i] - depth))
            else:
                idx = 0

            obs_depth = depths[idx]
            obs_temp = profile["temperatures"][idx]
            obs_sal = profile["salinities"][idx]
        else:
            if latitude is None or longitude is None or depth is None or time is None:
                raise ValueError("Either (platform_number, cycle_number) or explicit (latitude, longitude, depth, time) must be provided.")
            plat_id = "MANUAL_INPUT"
            cyc_id = 0
            obs_time = time
            obs_lat = latitude
            obs_lon = longitude
            obs_depth = depth
            obs_temp = observed_temperature
            obs_sal = observed_salinity

        # Query HYCOM model prediction at matched location, depth, and time
        hycom_temp_res = self.hycom_service.get_point("TEMP", obs_time, obs_lat, obs_lon, obs_depth)
        hycom_sal_res = self.hycom_service.get_point("SALN", obs_time, obs_lat, obs_lon, obs_depth)
        hycom_u_res = self.hycom_service.get_point("UVEL", obs_time, obs_lat, obs_lon, obs_depth)
        hycom_v_res = self.hycom_service.get_point("VVEL", obs_time, obs_lat, obs_lon, obs_depth)

        model_temp = hycom_temp_res["value"]
        model_sal = hycom_sal_res["value"]
        model_u = hycom_u_res["value"]
        model_v = hycom_v_res["value"]

        # Compute errors (model - observed)
        temp_err = (model_temp - obs_temp) if (model_temp is not None and obs_temp is not None) else None
        sal_err = (model_sal - obs_sal) if (model_sal is not None and obs_sal is not None) else None

        # Compute matching spatial-temporal metrics
        spatial_dist = haversine_distance_km(obs_lat, obs_lon, hycom_temp_res["actual_latitude"], hycom_temp_res["actual_longitude"])
        depth_diff = abs(obs_depth - hycom_temp_res["actual_depth"])

        t_obs_dt = to_datetime(obs_time, utc=True)
        t_mod_dt = to_datetime(hycom_temp_res["actual_time"], utc=True)
        time_diff_hours = abs((t_obs_dt - t_mod_dt).total_seconds()) / 3600.0

        return {
            "platform_number": plat_id,
            "cycle_number": cyc_id,
            "time": obs_time,
            "latitude": obs_lat,
            "longitude": obs_lon,
            "depth": obs_depth,

            "model_temperature": model_temp,
            "observed_temperature": obs_temp,
            "temperature_error": round(temp_err, 4) if temp_err is not None else None,

            "model_salinity": model_sal,
            "observed_salinity": obs_sal,
            "salinity_error": round(sal_err, 4) if sal_err is not None else None,

            "model_u": model_u,
            "model_v": model_v,

            "matching_metadata": {
                "spatial_distance_km": round(spatial_dist, 3),
                "depth_diff_m": round(depth_diff, 2),
                "time_diff_hours": round(time_diff_hours, 2),
                "interpolation_method": "nearest_trilinear_grid_search",
            }
        }
