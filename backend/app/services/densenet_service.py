"""
DenseNet + FAISS Similarity Search Service — Integration Placeholder

This module is a temporary adapter stub.
The actual DenseNet feature extractor + FAISS nearest-neighbour retrieval
is being developed by a teammate.

HOW TO INTEGRATE:
    When the teammate's DenseNet/FAISS implementation is ready, replace
    the body of `call_densenet()` with the real inference call.
    The function signature and return shape should stay the same.
"""


def call_densenet(image_bytes: bytes) -> dict:
    """
    Run DenseNet feature extraction and FAISS nearest-neighbour search
    to find historically similar X-ray cases.

    Args:
        image_bytes: Raw bytes of the uploaded image file.

    Returns:
        A dict with similar case results.

        Current (placeholder) shape:
            {
                "similar_cases": [],  # list of matched cases
                "status": "mock"      # indicates this is not a real prediction
            }

        Real implementation shape (to be defined by teammate):
            {
                "similar_cases": [
                    {"case_id": "CHX-00421", "similarity": 0.87, "diagnosis": "Pneumonia"},
                    ...
                ],
                "status": "ok"
            }

    TODO: Replace this stub with real DenseNet + FAISS retrieval.
    """
    # ── PLACEHOLDER — replace with real DenseNet + FAISS retrieval ──
    return {
        "similar_cases": [],
        "status": "mock",
    }
