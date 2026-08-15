"""
Multimodal Analysis Service — Integration Placeholder

This module is a temporary adapter stub.
The actual multimodal model (combining X-ray image + clinical text)
is being developed by a teammate.

HOW TO INTEGRATE:
    When the teammate's multimodal model is ready, replace the body of
    `call_multimodal()` with the real inference call.
    The function signature and return shape should stay the same.
"""

from typing import Optional


def call_multimodal(image_bytes: bytes, clinical_notes: Optional[str]) -> dict:
    """
    Run multimodal analysis combining the X-ray image and optional clinical notes.

    Args:
        image_bytes:    Raw bytes of the uploaded image file.
        clinical_notes: Optional free-text clinical context from the clinician.
                        May be None if no notes were provided.

    Returns:
        A dict with pathology probabilities and Grad-CAM data.

        Current (placeholder) shape:
            {
                "pathology_probabilities": {},  # per-pathology confidence scores
                "grad_cam": None,               # Grad-CAM heatmap (base64 or array)
                "status": "mock"
            }

        Real implementation shape (to be defined by teammate):
            {
                "pathology_probabilities": {
                    "Pneumonia": 0.82,
                    "Effusion": 0.14,
                    "Atelectasis": 0.04,
                },
                "grad_cam": "<base64-encoded heatmap>",
                "status": "ok"
            }

    TODO: Replace this stub with real multimodal model inference.
    """
    # ── PLACEHOLDER — replace with real multimodal model inference ──
    return {
        "pathology_probabilities": {},
        "grad_cam": None,
        "status": "mock",
    }
