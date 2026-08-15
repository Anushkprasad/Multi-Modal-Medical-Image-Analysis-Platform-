"""
CRUD helpers for the prediction_audit table.

Keeps all database logic out of the route handlers.
Routes call these functions; they never touch SQLAlchemy directly.
"""

import json
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import PredictionAudit


def save_audit(
    db: Session,
    *,
    request_id: str,
    filename: str,
    clinical_notes: Optional[str],
    yolo_result: dict,
    densenet_result: dict,
    multimodal_result: dict,
    gemini_report: dict,
) -> PredictionAudit:
    """
    Create and persist one audit record for a completed prediction request.

    Args:
        db:               SQLAlchemy session (injected by FastAPI dependency).
        request_id:       UUID string for this prediction.
        filename:         Original uploaded filename.
        clinical_notes:   Optional clinician text.
        yolo_result:      Dict from the YOLO service.
        densenet_result:  Dict from the DenseNet service.
        multimodal_result: Dict from the multimodal service.
        gemini_report:    Dict (RadiologyReport.model_dump()) from Gemini.

    Returns:
        The saved PredictionAudit ORM instance.
    """
    record = PredictionAudit(
        request_id=request_id,
        filename=filename,
        clinical_notes=clinical_notes,
        yolo_result=json.dumps(yolo_result),
        densenet_result=json.dumps(densenet_result),
        multimodal_result=json.dumps(multimodal_result),
        gemini_report=json.dumps(gemini_report),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_audit_by_request_id(
    db: Session,
    request_id: str,
) -> Optional[PredictionAudit]:
    """
    Fetch a single audit record by its request_id.

    Returns None if no matching record exists.
    """
    return (
        db.query(PredictionAudit)
        .filter(PredictionAudit.request_id == request_id)
        .first()
    )
