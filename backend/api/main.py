"""
backend/api/main.py
FastAPI Application Entry Point for INCOIS 3D Ocean Data Visualization Platform.
Configures lifespan handlers, CORS, routers, and structured exception handling.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.api.config import settings
from backend.api.dependencies import (
    get_dataset_service,
    get_hycom_service,
    get_vam_baseline_service,
)
from backend.api.routers import health, datasets, ocean, observations, hycom, baseline, compare


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application Lifespan Context Manager.
    Handles startup configuration and cleans up cached datasets on shutdown.
    """
    yield
    # Shutdown cleanup
    try:
        get_dataset_service().close_all_cached()
        get_hycom_service().close()
        get_vam_baseline_service().close()
    except Exception:
        pass


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Scientific Data Access API for INCOIS 3D Ocean Model Visualization & Digital Twin Services",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(health.router)
app.include_router(datasets.router)
app.include_router(hycom.router)
app.include_router(baseline.router)
app.include_router(compare.router)
app.include_router(ocean.router)
app.include_router(observations.router)


# Structured Error Handlers (Prevents stack trace leaks)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles Pydantic request validation errors (422)."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Request validation error", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches unhandled internal exceptions (500) without leaking stack traces."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the administrator."},
    )
