"""
backend/app/main.py
FastAPI Application Entry Point for OceanTwin 3D Platform.
Configures CORS middleware, route handlers, OpenAPI metadata, and exception handlers.
"""

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.routes import health, datasets, observations, ml

app = FastAPI(
    title="INCOIS OceanTwin 3D API Bridge",
    description="REST API connecting Next.js 14 3D Visualization Frontend with Python Ocean Science & ML Fusion Engine.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001")
allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Route Modules
app.include_router(health.router)
app.include_router(datasets.router)
app.include_router(observations.router)
app.include_router(ml.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler returning structured JSON errors without exposing internal stack traces."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": f"An unexpected server error occurred: {str(exc)}",
            "path": str(request.url.path)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
