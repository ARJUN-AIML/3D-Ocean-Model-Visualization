"""
backend/app/routes/datasets.py
Endpoints for dataset listing, 2D slice extraction, and velocity vectors.
"""

import math
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
import numpy as np

from backend.app.dependencies import get_dataset_manager, get_default_dataset
from backend.app.schemas import DatasetSummary, SliceResponse, VectorsResponse, VectorPoint
from backend.app.adapters import map_frontend_var_to_backend
from backend.science.slicing import OceanDataSlicer
from backend.science.canonical import VAR_U_CURRENT, VAR_V_CURRENT, VAR_TEMPERATURE, VAR_SALINITY

router = APIRouter(tags=["Datasets"])


@router.get("/api/datasets", response_model=List[DatasetSummary])
async def list_datasets():
    """Lists available registered ocean NetCDF/Zarr datasets."""
    dm = get_dataset_manager()
    raw_list = dm.list_datasets()
    result = []
    for item in raw_list:
        ds_id = item.get("dataset_id", "default")
        result.append(
            DatasetSummary(
                id=ds_id,
                name=item.get("name", f"Dataset {ds_id}"),
                description=f"Status: {item.get('data_status', 'SYNTHETIC')} | Size: {item.get('file_size_mb', 0)}MB",
                spatial_bounds={"min_lat": 10.0, "max_lat": 15.0, "min_lon": 70.0, "max_lon": 75.0},
                depth_levels=[0.0, 10.0, 50.0, 100.0, 200.0, 500.0, 1000.0, 2000.0],
                time_steps=["2026-09-01T00:00:00Z"],
                variables=["temp", "salinity", "currents", "waves"]
            )
        )
    if not result:
        result.append(
            DatasetSummary(
                id="indian_ocean_demo",
                name="Indian Ocean EEZ Synthetic ROMS Model Dataset",
                description="Default high-resolution synthetic ocean model field for Arabian Sea region.",
                spatial_bounds={"min_lat": 10.0, "max_lat": 15.0, "min_lon": 70.0, "max_lon": 75.0},
                depth_levels=[0.0, 10.0, 50.0, 100.0, 200.0, 500.0, 1000.0, 2000.0],
                time_steps=["2026-09-01T00:00:00Z"],
                variables=["temp", "salinity", "currents", "waves"]
            )
        )
    return result


@router.get("/api/datasets/{dataset_id}/slice", response_model=SliceResponse)
@router.get("/api/slice", response_model=SliceResponse)
async def get_slice(
    dataset_id: str = "default",
    variable: str = Query("temp", description="temp | salinity | currents | waves"),
    depth: float = Query(0.0, description="Depth level in meters"),
    time: Optional[str] = Query(None, description="ISO timestamp or time index")
):
    """Extracts a 2D spatial slice of requested variable at target depth and time step."""
    try:
        ds, _ = get_default_dataset()
        slicer = OceanDataSlicer(ds)

        cf_var = map_frontend_var_to_backend(variable)
        time_idx = int(time) if (time and time.isdigit()) else 0
        slice_result = slicer.extract_2d_slice(variable=cf_var, depth=depth, time_index=time_idx)

        grid_values = slice_result["data_grid"]
        clean_grid = []
        for row in grid_values:
            clean_row = []
            for val in row:
                if val is None or np.isnan(val) or np.isinf(val):
                    clean_row.append(None)
                else:
                    clean_row.append(round(float(val), 3))
            clean_grid.append(clean_row)

        return SliceResponse(
            datasetId=dataset_id,
            variable=variable,
            depth=float(slice_result["depth_actual"]),
            time=str(slice_result["time_actual"]),
            minVal=round(float(slice_result["min_val"]), 2),
            maxVal=round(float(slice_result["max_val"]), 2),
            units=str(slice_result["units"]),
            latitudes=[round(float(lat), 4) for lat in slice_result["latitude"]],
            longitudes=[round(float(lon), 4) for lon in slice_result["longitude"]],
            values=clean_grid
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Slice extraction error: {str(e)}")


@router.get("/api/datasets/{dataset_id}/vectors", response_model=VectorsResponse)
@router.get("/api/vectors", response_model=VectorsResponse)
async def get_vectors(
    dataset_id: str = "default",
    depth: float = Query(0.0, description="Depth level in meters"),
    time: Optional[str] = Query(None, description="ISO timestamp or time index"),
    stride: int = Query(1, description="Subsampling stride")
):
    """Subsamples horizontal current velocity vectors (u, v) for rendering animated current fields."""
    try:
        dm = get_dataset_manager()
        ds = dm.get_dataset(dataset_id) if (dataset_id and dataset_id != "default" and dataset_id in getattr(dm, 'datasets', {})) else get_default_dataset()[0]
        slicer = OceanDataSlicer(ds)
        time_idx = int(time) if (time and time.isdigit()) else 0
        vec_data = slicer.extract_velocity_vectors(depth=depth, time_index=time_idx, stride=stride)

        vectors = []
        u_grid = np.array(vec_data["u"], dtype=float)
        v_grid = np.array(vec_data["v"], dtype=float)
        lats = vec_data["latitude"]
        lons = vec_data["longitude"]

        for i in range(len(lats)):
            for j in range(len(lons)):
                if i < u_grid.shape[0] and j < u_grid.shape[1]:
                    u_val = float(u_grid[i, j])
                    v_val = float(v_grid[i, j])
                    if not (np.isnan(u_val) or np.isnan(v_val)):
                        speed = math.sqrt(u_val**2 + v_val**2)
                        direction = (math.degrees(math.atan2(u_val, v_val)) + 360) % 360
                        vectors.append(
                            VectorPoint(
                                lat=round(float(lats[i]), 4),
                                lon=round(float(lons[j]), 4),
                                u=round(u_val, 3),
                                v=round(v_val, 3),
                                speed=round(speed, 3),
                                directionDeg=round(direction, 1)
                            )
                        )

        return VectorsResponse(
            datasetId=dataset_id,
            depth=depth,
            time=str(vec_data["time_actual"]),
            vectorCount=len(vectors),
            vectors=vectors
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Vectors extraction error: {str(e)}")

