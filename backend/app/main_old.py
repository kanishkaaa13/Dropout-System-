"""
main.py
───────
FastAPI application entrypoint for the JEE Dropout Prediction System.

Start the dev server:
    uvicorn backend.app.main:app --reload --port 8000

API docs available at:
    http://localhost:8000/api/docs     (Swagger UI)
    http://localhost:8000/api/redoc   (ReDoc)
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings

# ── Application Start Time for Uptime Calculation ───────────────────────────

APP_START_TIME = time.time()

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan: load ML models once at startup ──────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Modern FastAPI lifespan context manager.

    On startup:
      1. Create all DB tables (dev convenience; use Alembic in production)
      2. Load ML models + initialise SHAP explainer
      3. Store references on app.state for router access

    On shutdown:
      Logs a clean shutdown message.
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("== JEE Dropout Prediction API starting up ==")

    # Create DB tables (SQLite dev mode)
    try:
        from backend.app.database import create_all_tables
        create_all_tables()
        logger.info("Database tables verified / created.")
    except Exception as exc:
        logger.error("DB table creation failed: %s", exc)

    # Resolve model directory — prefer real-dataset models if available
    real_model_dir      = os.path.abspath(os.path.join(settings.MODEL_DIR, "real"))
    synthetic_model_dir = os.path.abspath(settings.MODEL_DIR)

    model_dir = real_model_dir if os.path.exists(
        os.path.join(real_model_dir, "xgb_model.pkl")
    ) else synthetic_model_dir

    # Load predictor
    try:
        from backend.app.ml.predictor import JEEDropoutPredictor

        predictor = JEEDropoutPredictor(
            model_dir=model_dir,
            threshold=settings.PREDICTION_THRESHOLD,
        )
        predictor.load_models()
        app.state.predictor = predictor
        app.state.ml_pipeline = predictor.pipeline   # "real" or "synthetic"
        logger.info(
            "ML models loaded from '%s' | pipeline=%s | version=%s",
            model_dir,
            predictor.pipeline,
            predictor.metadata.get("version", "?"),
        )
    except FileNotFoundError as exc:
        logger.error("ML model files not found: %s", exc)
        logger.error(
            "Run 'python ml_training/train.py' or 'python ml_training/train_real_dataset.py' first."
        )
        app.state.predictor  = None
        app.state.ml_pipeline = "none"

    # Load SHAP explainer (depends on predictor being loaded)
    if app.state.predictor is not None:
        try:
            from backend.app.ml.explainer import SHAPExplainer

            explainer = SHAPExplainer(
                shap_explainer=app.state.predictor.get_shap_explainer(),
                preprocessor=app.state.predictor.get_preprocessor(),
                feature_cols=app.state.predictor.feature_cols,
                top_n=10,
            )
            app.state.explainer = explainer
            logger.info("SHAP explainer initialised.")
        except Exception as exc:
            logger.error("SHAP explainer initialisation failed: %s", exc)
            app.state.explainer = None
    else:
        app.state.explainer = None

    # Start background scheduler
    try:
        from backend.app.services.scheduler import start_scheduler
        start_scheduler()
        logger.info("Background scheduler started.")
    except Exception as exc:
        logger.error("Scheduler startup failed: %s", exc)

    logger.info("Startup complete. API is ready.")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    try:
        from backend.app.services.scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass
    logger.info("== JEE Dropout Prediction API shutting down ==")


# ── Application factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
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

    # ── Audit logging middleware ───────────────────────────────────────
    from backend.app.middleware.audit import AuditMiddleware
    app.add_middleware(AuditMiddleware, exclude_paths=["/health", "/metrics"])

    # ── Rate limiting (SlowAPI) ─────────────────────────────────────────
    try:
        from backend.app.middleware.rate_limiter import setup_rate_limiter
        setup_rate_limiter(app)
    except ImportError:
        logger.warning("slowapi not installed — rate limiting disabled")

    # ── Global exception handlers ─────────────────────────────────────────────

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected server error occurred.",
                "path": str(request.url),
            },
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    from backend.app.routers.auth           import router as auth_router
    from backend.app.routers.students       import router as students_router
    from backend.app.routers.prediction     import router as prediction_router
    from backend.app.routers.alerts         import router as alerts_router
    from backend.app.routers.reports        import router as reports_router
    from backend.app.routers.chat           import router as chat_router
    from backend.app.routers.interventions  import router as interventions_router
    from backend.app.routers.demo           import router as demo_router

    API_PREFIX = "/api/v1"

    app.include_router(auth_router,          prefix=API_PREFIX)
    app.include_router(students_router,      prefix=API_PREFIX)
    app.include_router(prediction_router,    prefix=API_PREFIX)
    app.include_router(alerts_router,        prefix=API_PREFIX)
    app.include_router(reports_router,       prefix=API_PREFIX)
    app.include_router(chat_router,          prefix=API_PREFIX)
    app.include_router(interventions_router, prefix=API_PREFIX)
    app.include_router(demo_router,          prefix=API_PREFIX)

    # ── Health check with uptime and model version ───────────────────────────────

    @app.get("/health", tags=["System"], include_in_schema=False)
    async def health_check(request: Request) -> dict:
        predictor = getattr(request.app.state, "predictor", None)
        uptime_seconds = time.time() - APP_START_TIME
        uptime_hours = uptime_seconds / 3600
        
        model_info = {}
        if predictor is not None and predictor.is_loaded:
            model_info = {
                "model_version": predictor.metadata.get("version", "unknown"),
                "pipeline": predictor.pipeline,
                "n_features": predictor.metadata.get("n_features", 0),
                "threshold": predictor.metadata.get("threshold", 0.5),
                "trained_at": predictor.metadata.get("trained_at", "unknown"),
            }
        
        return {
            "status": "ok",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "uptime_seconds": round(uptime_seconds, 2),
            "uptime_hours": round(uptime_hours, 2),
            "ml_models_loaded": predictor is not None and predictor.is_loaded,
            "model_info": model_info,
        }

    @app.get("/", tags=["System"], include_in_schema=False)
    async def root() -> dict:
        return {
            "name":    settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs":    "/api/docs",
        }

    return app


# ── Module-level app instance (used by uvicorn) ───────────────────────────────
app = create_app()
