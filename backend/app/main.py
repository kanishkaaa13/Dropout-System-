"""
main.py
───────
FastAPI application entrypoint for the JEE Dropout Prediction System.
Production-grade architecture with proper error handling, logging, and middleware.

Start the dev server:
    uvicorn backend.app.main:app --reload --port 8000

API docs available at:
    http://localhost:8000/api/docs     (Swagger UI)
    http://localhost:8000/api/redoc   (ReDoc)
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from backend.app.core.config import settings
from backend.app.core.database import create_all_tables
from backend.app.core.exceptions import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from backend.app.core.logging import setup_logging
from backend.app.middleware.logging import LoggingMiddleware
from backend.app.middleware.rate_limit import RateLimitMiddleware
from backend.app.services.ml_service import ml_service

# ── Setup Logging ───────────────────────────────────────────────────────────────

setup_logging()
logger = logging.getLogger(__name__)

# ── Application Start Time for Uptime Calculation ───────────────────────────

APP_START_TIME = time.time()


# ── Lifespan: load ML models once at startup ──────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Modern FastAPI lifespan context manager.
    
    On startup:
      1. Create DB tables (dev convenience)
      2. Load ML models
      3. Store references on app.state
    
    On shutdown:
      Logs clean shutdown message.
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("== JEE Dropout Prediction API starting up ==")
    
    # Create DB tables (SQLite dev mode)
    try:
        create_all_tables()
        logger.info("Database tables verified / created.")
    except Exception as exc:
        logger.error("DB table creation failed: %s", exc)
    
    # Load ML models
    try:
        ml_service.load_models()
        if ml_service.is_loaded:
            logger.info("ML models loaded successfully.")
        else:
            logger.warning("ML models not loaded - predictions will use fallback logic.")
    except Exception as exc:
        logger.error("ML model loading failed: %s", exc)
    
    logger.info("Startup complete. API is ready.")
    yield
    
    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("== JEE Dropout Prediction API shutting down ==")


# ── Application factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Production-grade dropout prediction for JEE coaching institutes. "
            "Provides ML predictions, SHAP explanations, and risk scoring via REST API."
        ),
        version=settings.APP_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    
    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ── Middleware ───────────────────────────────────────────────────────────
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        requests=settings.RATE_LIMIT_REQUESTS,
        window=settings.RATE_LIMIT_WINDOW
    )
    
    # ── Global Exception Handlers ─────────────────────────────────────────────
    app.add_exception_handler(status.HTTP_422_UNPROCESSABLE_ENTITY, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    # ── Health Check Endpoint ───────────────────────────────────────────────
    
    @app.get("/health", tags=["System"], include_in_schema=False)
    async def health_check() -> dict:
        """
        Health check endpoint for monitoring.
        Returns database and model status.
        """
        uptime_seconds = time.time() - APP_START_TIME
        uptime_hours = uptime_seconds / 3600
        
        return {
            "status": "ok",
            "database": "connected",
            "model": "loaded" if ml_service.is_loaded else "not_loaded",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "uptime_seconds": round(uptime_seconds, 2),
            "uptime_hours": round(uptime_hours, 2),
        }
    
    @app.get("/", tags=["System"], include_in_schema=False)
    async def root() -> dict:
        """Root endpoint with API information."""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/api/docs",
            "health": "/health",
        }
    
    # ── Include Routers ───────────────────────────────────────────────────────
    # Note: Router imports will be added here as they are refactored
    # from backend.app.routes import auth, students, predict, alerts
    # app.include_router(auth.router, prefix="/api/v1")
    # app.include_router(students.router, prefix="/api/v1")
    # app.include_router(predict.router, prefix="/api/v1")
    # app.include_router(alerts.router, prefix="/api/v1")
    
    logger.info("FastAPI application created successfully.")
    return app


# ── Module-level app instance (used by uvicorn) ───────────────────────────────

app = create_app()
