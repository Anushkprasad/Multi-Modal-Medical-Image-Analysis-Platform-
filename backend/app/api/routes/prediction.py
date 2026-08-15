"""
Prediction API Routes

All endpoints live under the /api/v1 prefix.

Endpoints:
    POST /api/v1/predict             — Full pipeline: upload → models → Gemini → audit.
    GET  /api/v1/health              — Backend + DB health check.
    GET  /api/v1/audit/{request_id}  — Retrieve one audit record.
"""

import json
import uuid
from typing import Optional

import sqlalchemy
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import crud
from app.db.database import get_db
from app.schemas.prediction import AuditRecord, PredictionResponse
from app.services.densenet_service import call_densenet
from app.services.gemini_service import generate_report
from app.services.multimodal_service import call_multimodal
from app.services.yolo_service import call_yolo

router = APIRouter(
    prefix="/api/v1",
    tags=["Prediction"],
)

# Only these MIME types are accepted as X-ray images
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png"}


# ── POST /api/v1/predict ────────────────────────────────────────
@router.post("/predict", response_model=PredictionResponse, summary="Run prediction pipeline")
async def predict(
    image: UploadFile = File(..., description="X-ray image file (JPEG or PNG)"),
    clinical_notes: Optional[str] = Form(None, description="Optional clinical context text"),
    db: Session = Depends(get_db),
) -> PredictionResponse:
    """
    Full prediction pipeline for an uploaded X-ray image.

    **Request**: multipart/form-data
    - `image`          — JPEG or PNG X-ray image (required)
    - `clinical_notes` — Free-text clinical notes from the clinician (optional)

    **Steps executed**:
    1. Validate that the uploaded file is an allowed image type.
    2. Call YOLO detection service (placeholder).
    3. Call DenseNet/FAISS similarity service (placeholder).
    4. Call Multimodal analysis service (placeholder).
    5. Send all model outputs to Gemini for structured report generation.
    6. Save the complete audit record to the database.
    7. Return the full prediction response including a unique `request_id`.

    **Returns HTTP 400** if the file type is not supported.
    """
    # ── 1. Validate file type ────────────────────────────────────
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: '{image.content_type}'. "
                f"Accepted types: {', '.join(sorted(ALLOWED_IMAGE_TYPES))}"
            ),
        )

    # ── 2. Read image bytes ──────────────────────────────────────
    image_bytes: bytes = await image.read()

    # ── 3–5. Call model services (currently placeholders) ────────
    yolo_result = call_yolo(image_bytes)
    densenet_result = call_densenet(image_bytes)
    multimodal_result = call_multimodal(image_bytes, clinical_notes)

    # ── 6. Generate structured Gemini report ─────────────────────
    gemini_report = generate_report(
        yolo_result=yolo_result,
        densenet_result=densenet_result,
        multimodal_result=multimodal_result,
        clinical_notes=clinical_notes,
    )

    # ── 7. Assign unique request ID ──────────────────────────────
    request_id = str(uuid.uuid4())

    # ── 8. Persist audit record ──────────────────────────────────
    crud.save_audit(
        db=db,
        request_id=request_id,
        filename=image.filename or "unknown",
        clinical_notes=clinical_notes,
        yolo_result=yolo_result,
        densenet_result=densenet_result,
        multimodal_result=multimodal_result,
        gemini_report=gemini_report.model_dump(),
    )

    # ── 9. Return response ───────────────────────────────────────
    return PredictionResponse(
        request_id=request_id,
        filename=image.filename or "unknown",
        yolo_result=yolo_result,
        densenet_result=densenet_result,
        multimodal_result=multimodal_result,
        gemini_report=gemini_report,
    )


# ── GET /api/v1/health ──────────────────────────────────────────
@router.get("/health", summary="API and database health check")
def api_health(db: Session = Depends(get_db)) -> dict:
    """
    Check whether the backend and database are reachable.

    Never raises an exception — if the DB is unavailable the response
    will show `"database": "unavailable: <reason>"` instead of crashing.
    """
    db_status: str
    try:
        db.execute(sqlalchemy.text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"unavailable: {exc}"

    return {
        "status": "healthy",
        "database": db_status,
    }


# ── GET /api/v1/audit/{request_id} ──────────────────────────────
@router.get(
    "/audit/{request_id}",
    response_model=AuditRecord,
    summary="Retrieve a prediction audit record",
)
def get_audit(request_id: str, db: Session = Depends(get_db)) -> AuditRecord:
    """
    Retrieve the audit record saved after a previous prediction request.

    Args:
        request_id: The UUID string returned by POST /api/v1/predict.

    Returns HTTP 404 if no record with that `request_id` exists.
    """
    record = crud.get_audit_by_request_id(db, request_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"No audit record found for request_id='{request_id}'.",
        )

    # Decode JSON text columns back into dicts for the response
    return AuditRecord(
        id=record.id,
        request_id=record.request_id,
        filename=record.filename,
        clinical_notes=record.clinical_notes,
        yolo_result=json.loads(record.yolo_result) if record.yolo_result else None,
        densenet_result=json.loads(record.densenet_result) if record.densenet_result else None,
        multimodal_result=json.loads(record.multimodal_result) if record.multimodal_result else None,
        gemini_report=json.loads(record.gemini_report) if record.gemini_report else None,
        created_at=str(record.created_at) if record.created_at else None,
    )