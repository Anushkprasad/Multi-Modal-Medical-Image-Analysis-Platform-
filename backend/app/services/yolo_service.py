"""
YOLO Object Detection Service — Integration Placeholder

This module is a temporary adapter stub.
The actual YOLO model is being developed by a teammate.

HOW TO INTEGRATE:
    When the teammate's YOLO model is ready, replace the body of
    `call_yolo()` with the real inference call.
    The function signature and return shape should stay the same
    so the prediction route does not need to change.
"""


def call_yolo(image_bytes: bytes) -> dict:
    """
    Run YOLO object detection on the supplied X-ray image.

    Args:
        image_bytes: Raw bytes of the uploaded image file.

    Returns:
        A dict with detection results.

        Current (placeholder) shape:
            {
                "detections": [],   # list of bounding boxes / labels
                "status": "mock"    # indicates this is not a real prediction
            }

        Real implementation shape (to be defined by teammate):
            {
                "detections": [
                    {"label": "nodule", "confidence": 0.91, "bbox": [x, y, w, h]},
                    ...
                ],
                "status": "ok"
            }

    TODO: Replace this stub with real YOLO model inference.
    """
    # ── PLACEHOLDER — replace with real YOLO inference ──────────
    return {
        "detections": [],
        "status": "mock",
    }
