"""
backend/api/services/argo_service.py
Service for querying, indexing, and filtering cleaned INCOIS Indian Argo observation profiles.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from backend.api.config import settings

logger = logging.getLogger(__name__)


class ArgoService:
    def __init__(self, csv_path: Optional[str] = None):
        self.csv_path = csv_path or settings.ARGO_DATA_PATH
        self._df: Optional[pd.DataFrame] = None

    def _load_data(self) -> pd.DataFrame:
        """Load and cache clean Argo CSV dataframe in memory."""
        if self._df is None:
            if not os.path.exists(self.csv_path):
                raise FileNotFoundError(f"Clean Argo dataset not found at: {self.csv_path}")
            
            logger.info(f"Loading cleaned Argo dataset from: {self.csv_path}")
            df = pd.read_csv(self.csv_path, low_memory=False)
            df['PLATFORM_NUMBER'] = df['PLATFORM_NUMBER'].astype(str).str.replace(r'\.0$', '', regex=True)
            df['CYCLE_NUMBER'] = pd.to_numeric(df['CYCLE_NUMBER'], errors='coerce').fillna(0).astype(int)
            df['time_dt'] = pd.to_datetime(df['time'], errors='coerce', utc=True)
            self._df = df
        return self._df

    def get_summary(self) -> Dict[str, Any]:
        """Return dataset statistics, float count, and spatial-temporal range."""
        df = self._load_data()
        platforms = sorted(df['PLATFORM_NUMBER'].unique().tolist())
        cycles_count = len(df[['PLATFORM_NUMBER', 'CYCLE_NUMBER']].drop_duplicates())

        return {
            "dataset_id": os.path.basename(self.csv_path),
            "source": "INCOIS Indian Argo Floats (Cleaned)",
            "total_observations": len(df),
            "total_platforms": len(platforms),
            "total_profiles": cycles_count,
            "time_start": df['time_dt'].min().isoformat() if not df.empty else None,
            "time_end": df['time_dt'].max().isoformat() if not df.empty else None,
            "lat_min": float(df['latitude'].min()),
            "lat_max": float(df['latitude'].max()),
            "lon_min": float(df['longitude'].min()),
            "lon_max": float(df['longitude'].max()),
            "depth_min": float(df['depth_m'].min()),
            "depth_max": float(df['depth_m'].max()),
            "platforms": platforms[:50],  # sample platforms
        }

    def get_observations(
        self,
        platform_number: Optional[str] = None,
        cycle_number: Optional[int] = None,
        lat_min: Optional[float] = None,
        lat_max: Optional[float] = None,
        lon_min: Optional[float] = None,
        lon_max: Optional[float] = None,
        depth_min: Optional[float] = None,
        depth_max: Optional[float] = None,
        time_start: Optional[str] = None,
        time_end: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Filter Argo observations by platform, cycle, spatial bounding box, and datetime range."""
        df = self._load_data()
        mask = np.ones(len(df), dtype=bool)

        if platform_number is not None:
            clean_plat = str(platform_number).strip().replace(".0", "")
            mask &= (df['PLATFORM_NUMBER'] == clean_plat)

        if cycle_number is not None:
            mask &= (df['CYCLE_NUMBER'] == int(cycle_number))

        if lat_min is not None:
            mask &= (df['latitude'] >= float(lat_min))
        if lat_max is not None:
            mask &= (df['latitude'] <= float(lat_max))

        if lon_min is not None:
            mask &= (df['longitude'] >= float(lon_min))
        if lon_max is not None:
            mask &= (df['longitude'] <= float(lon_max))

        if depth_min is not None:
            mask &= (df['depth_m'] >= float(depth_min))
        if depth_max is not None:
            mask &= (df['depth_m'] <= float(depth_max))

        if time_start is not None:
            t_start = pd.to_datetime(time_start, utc=True)
            mask &= (df['time_dt'] >= t_start)
        if time_end is not None:
            t_end = pd.to_datetime(time_end, utc=True)
            mask &= (df['time_dt'] <= t_end)

        filtered = df[mask]
        total_matched = len(filtered)

        sliced = filtered.iloc[offset : offset + limit]

        records = []
        for _, row in sliced.iterrows():
            records.append({
                "platform_number": str(row['PLATFORM_NUMBER']),
                "cycle_number": int(row['CYCLE_NUMBER']),
                "time": str(row['time']),
                "latitude": float(row['latitude']),
                "longitude": float(row['longitude']),
                "pressure_adjusted": float(row['PRES_ADJUSTED']),
                "pressure_qc": int(row['PRES_ADJUSTED_QC']),
                "temperature_adjusted": float(row['TEMP_ADJUSTED']),
                "temperature_qc": int(row['TEMP_ADJUSTED_QC']),
                "salinity_adjusted": float(row['PSAL_ADJUSTED']),
                "salinity_qc": int(row['PSAL_ADJUSTED_QC']),
                "depth_m": float(row['depth_m']),
            })

        return {
            "source": "INCOIS Indian Argo Floats (Cleaned)",
            "total_matched": total_matched,
            "limit": limit,
            "offset": offset,
            "observations": records,
        }

    def get_profile(
        self,
        platform_number: str,
        cycle_number: int,
    ) -> Dict[str, Any]:
        """Extract complete vertical depth profile for a single float cycle."""
        df = self._load_data()
        clean_plat = str(platform_number).strip().replace(".0", "")
        mask = (df['PLATFORM_NUMBER'] == clean_plat) & (df['CYCLE_NUMBER'] == int(cycle_number))

        profile_df = df[mask].sort_values("depth_m")
        if profile_df.empty:
            raise KeyError(f"No profile found for platform '{platform_number}', cycle {cycle_number}.")

        first = profile_df.iloc[0]
        
        return {
            "source": "INCOIS Indian Argo Floats (Cleaned)",
            "platform_number": clean_plat,
            "cycle_number": int(cycle_number),
            "time": str(first['time']),
            "latitude": float(first['latitude']),
            "longitude": float(first['longitude']),
            "total_measurements": len(profile_df),
            "depths": profile_df['depth_m'].tolist(),
            "temperatures": profile_df['TEMP_ADJUSTED'].tolist(),
            "salinities": profile_df['PSAL_ADJUSTED'].tolist(),
            "pressures": profile_df['PRES_ADJUSTED'].tolist(),
        }
