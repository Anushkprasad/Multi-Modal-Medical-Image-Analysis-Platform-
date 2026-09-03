"""
FastAPI application entry point.

Run from the backend/ directory:
    python -m uvicorn app.main:app --reload

Swagger UI available at:
    http://localhost:8000/docs

Environment variables are loaded from backend/.env (if present) before
any other module is imported, so settings like GEMINI_MOCK and DATABASE_URL
are available to all services at startup.
"""

# ── Load .env FIRST, before any other app imports ───────────────
# This ensures GEMINI_MOCK, GEMINI_API_KEY, DATABASE_URL, etc. are in
# os.environ before gemini_service.py or database.py read them.
from dotenv import load_dotenv

load_dotenv()  # reads backend/.env if it exists; safe no-op if it doesn't

# ── Now import the rest of the app ──────────────────────────────
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.prediction import router as prediction_router
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Creates database tables at startup (safe to run multiple times).
    """
    init_db()
    yield
    # Nothing to clean up on shutdown


app = FastAPI(
    title="Multi-Modal Medical Image Analysis API",
    version="0.1.0",
    description=(
        "Backend API for the Multi-Modal Medical Image Analysis Platform. "
        "Accepts X-ray images, runs AI model pipelines (YOLO, DenseNet, Multimodal), "
        "generates a structured radiology report via Gemini, and logs every prediction."
    ),
    lifespan=lifespan,
)


@app.get("/", tags=["Status"], summary="Root — API liveness check")
def root() -> dict:
    """Confirm the API is running."""
    return {"message": "Multi-Modal Medical Image Analysis API is running"}


@app.get("/health", tags=["Status"], summary="Simple health check")
def health_check() -> dict:
    """Simple liveness probe — no DB check."""
    return {"status": "healthy"}


# Register all prediction/audit/health endpoints under /api/v1
app.include_router(prediction_router)