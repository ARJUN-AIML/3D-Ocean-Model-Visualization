"""
backend/app/routes/waves.py
Endpoints for querying wave parameters strictly from Dataset 06 (06_wave_samples.csv).
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from backend.science.dataset_loader import get_wave_samples_data
from backend.app.schemas import WaveResponse, WaveSamplePoint, ProvenanceInfo

router = APIRouter(tags=["Wave Data Engine"])


@router.get("/api/waves", response_model=WaveResponse)
async def get_wave_data(
    min_lat: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    min_lon: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None),
    limit: int = Query(200, description="Max wave sample points to return")
):
    """Retrieves wave parameters (Significant Wave Height, Peak Period, Mean Direction) from Dataset 06."""
    try:
        df = get_wave_samples_data()
        filtered = df.copy()

        if min_lat is not None:
            filtered = filtered[filtered["lat"] >= min_lat]
        if max_lat is not None:
            filtered = filtered[filtered["lat"] <= max_lat]
        if min_lon is not None:
            filtered = filtered[filtered["lon"] >= min_lon]
        if max_lon is not None:
            filtered = filtered[filtered["lon"] <= max_lon]

        sample_df = filtered.head(limit)

        points = []
        for _, row in sample_df.iterrows():
            period_val = row.get("peak_wave_period_sec", row.get("peak_wave_period_s", 8.0))
            points.append(
                WaveSamplePoint(
                    lat=round(float(row["lat"]), 4),
                    lon=round(float(row["lon"]), 4),
                    timestamp=str(row.get("time_utc", row.get("timestamp_utc", "2026-08-23T00:00:00Z"))),
                    significantWaveHeightM=round(float(row["significant_wave_height_m"]), 2),
                    peakWavePeriodS=round(float(period_val), 1),
                    meanWaveDirectionDeg=round(float(row["mean_wave_direction_deg"]), 1)
                )
            )

        return WaveResponse(
            datasetId="06_wave_samples",
            count=len(points),
            waves=points,
            provenance=ProvenanceInfo(
                dataset_type="synthetic",
                source="OceanTwin Synthetic Demo Dataset (Dataset 06)",
                dataset_id="06_wave_samples",
                region="Indian Ocean / Arabian Sea"
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Wave dataset extraction error: {str(e)}")
