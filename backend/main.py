"""
backend/main.py
────────────────
FastAPI application entrypoint.

Creates the app instance, registers middleware, mounts routers,
and sets up startup/shutdown lifecycle events.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os

from backend.app.api.routes import router
from backend.app.core.config import settings
from backend.app.db.session import Base, engine

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup:
      1. Create all database tables (idempotent — safe to run repeatedly)
      2. Log configuration summary

    Application shutdown:
      - Dispose database connection pool
    """
    logger.info("=== Stock Analysis Agent starting up ===")
    logger.info(f"Environment : {settings.app_env}")
    logger.info(f"Database    : {settings.database_url.split('@')[-1]}")  # Hide credentials
    logger.info(f"Finnhub key : {'set' if settings.finnhub_api_key else 'not set (using mock data)'}")

    # Auto-create tables (in production, prefer Alembic migrations)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified.")

    yield  # ← Application runs here

    # Shutdown
    engine.dispose()
    logger.info("=== Stock Analysis Agent shut down ===")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Stock Analysis Agent",
    description=(
        "Production-ready stock analysis API implementing the Boni Womack strategy. "
        "Aggregates analyst recommendations, computes consensus scores & momentum, "
        "ranks stocks within industries, and generates BUY/SELL/HOLD signals."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(router)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check logs for details."},
    )

# ── Serve frontend dashboard ──────────────────────────────────────────────────
@app.get("/dashboard", include_in_schema=False)
def serve_dashboard():
    """Serve the dashboard HTML so it runs same-origin as the API."""
    dashboard_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "frontend", "dashboard.html")
    )
    return FileResponse(dashboard_path)
