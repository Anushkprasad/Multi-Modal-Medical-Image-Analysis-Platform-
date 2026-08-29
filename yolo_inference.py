"""
yolo_inference.py - YOLOv8 Pneumonia Detection Inference Module

Provides the main API function `predict_pneumonia()` that takes an image path
and returns a structured dictionary with detection results including bounding
boxes, confidence scores, and a base64-encoded annotated image.

Usage:
    from yolo_inference import predict_pneumonia
    result = predict_pneumonia("path/to/xray.png", conf_thresh=0.25)

    # Or run directly:
    python yolo_inference.py --image path/to/xray.png --weights weights/best.pt
"""

import os
import sys
import base64
import argparse
from typing import Optional

import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None


# Default path to trained weights
DEFAULT_WEIGHTS = os.path.join(os.path.dirname(__file__), "weights", "best.pt")

# Class mapping
CLASS_NAMES = {0: "Pneumonia"}


def predict_pneumonia(
    image_path: str,
    conf_thresh: float = 0.25,
    weights_path: str = DEFAULT_WEIGHTS,
    model: Optional[object] = None,
) -> dict:
    """
    Run YOLOv8 pneumonia detection on a chest X-ray image.

    Args:
        image_path: Path to the input X-ray image (PNG, JPEG, or DICOM).
        conf_thresh: Minimum confidence threshold for detections (default: 0.25).
        weights_path: Path to the trained YOLOv8 weights file (default: weights/best.pt).
        model: Optional pre-loaded YOLO model instance (avoids reloading on each call).

    Returns:
        Dictionary with the following schema:
        {
            "status": "success" | "error",
            "detection_count": int,
            "image_dimensions": {"width": int, "height": int},
            "detections": [
                {
                    "class_id": int,
                    "class_name": str,
                    "confidence": float,
                    "bbox_pixel": {"xmin": int, "ymin": int, "xmax": int, "ymax": int},
                    "bbox_normalized": {"xmin": float, "ymin": float, "xmax": float, "ymax": float}
                },
                ...
            ],
            "annotated_image_base64": str
        }
    """
    try:
        # ------------------------------------------------------------------
        # 1. Validate inputs
        # ------------------------------------------------------------------
        if not os.path.exists(image_path):
            return {
                "status": "error",
                "message": f"Image file not found: {image_path}",
                "detection_count": 0,
                "image_dimensions": {"width": 0, "height": 0},
                "detections": [],
                "annotated_image_base64": "",
            }

        # ------------------------------------------------------------------
        # 2. Load image
        # ------------------------------------------------------------------
        image = cv2.imread(image_path)
        if image is None:
            return {
                "status": "error",
                "message": f"Failed to read image: {image_path}",
                "detection_count": 0,
                "image_dimensions": {"width": 0, "height": 0},
                "detections": [],
                "annotated_image_base64": "",
            }

        img_h, img_w = image.shape[:2]

        # ------------------------------------------------------------------
        # 3. Load YOLO model
        # ------------------------------------------------------------------
        if model is None:
            if YOLO is None:
                return {
                    "status": "error",
                    "message": "ultralytics package is not installed. Run: pip install ultralytics",
                    "detection_count": 0,
                    "image_dimensions": {"width": img_w, "height": img_h},
                    "detections": [],
                    "annotated_image_base64": "",
                }
            if not os.path.exists(weights_path):
                return {
                    "status": "error",
                    "message": f"Model weights not found: {weights_path}. Train the model first using train.py.",
                    "detection_count": 0,
                    "image_dimensions": {"width": img_w, "height": img_h},
                    "detections": [],
                    "annotated_image_base64": "",
                }
            model = YOLO(weights_path)

        # ------------------------------------------------------------------
        # 4. Run inference
        # ------------------------------------------------------------------
        results = model.predict(
            source=image_path,
            conf=conf_thresh,
            verbose=False,
        )

        # ------------------------------------------------------------------
        # 5. Parse detections
        # ------------------------------------------------------------------
        detections = []
        annotated_image = image.copy()

        if results and len(results) > 0:
            result = results[0]
            boxes = result.boxes

            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    # Extract bounding box in pixel coordinates (xyxy format)
                    xyxy = box.xyxy[0].cpu().numpy()
                    xmin, ymin, xmax, ymax = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])

                    # Normalized coordinates
                    xmin_n = float(xyxy[0]) / img_w
                    ymin_n = float(xyxy[1]) / img_h
                    xmax_n = float(xyxy[2]) / img_w
                    ymax_n = float(xyxy[3]) / img_h

                    # Class and confidence
                    class_id = int(box.cls[0].cpu().numpy())
                    confidence = float(box.conf[0].cpu().numpy())
                    class_name = CLASS_NAMES.get(class_id, f"class_{class_id}")

                    detection = {
                        "class_id": class_id,
                        "class_name": class_name,
                        "confidence": round(confidence, 4),
                        "bbox_pixel": {
                            "xmin": xmin,
                            "ymin": ymin,
                            "xmax": xmax,
                            "ymax": ymax,
                        },
                        "bbox_normalized": {
                            "xmin": round(xmin_n, 6),
                            "ymin": round(ymin_n, 6),
                            "xmax": round(xmax_n, 6),
                            "ymax": round(ymax_n, 6),
                        },
                    }
                    detections.append(detection)

                    # ----------------------------------------------------------
                    # Draw bounding box overlay on annotated image
                    # ----------------------------------------------------------
                    color = (0, 0, 255)  # Red for pneumonia
                    thickness = 2
                    cv2.rectangle(
                        annotated_image,
                        (xmin, ymin),
                        (xmax, ymax),
                        color,
                        thickness,
                    )

                    # Label with class name and confidence
                    label = f"{class_name} {confidence:.2f}"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.6
                    font_thickness = 1
                    (label_w, label_h), baseline = cv2.getTextSize(
                        label, font, font_scale, font_thickness
                    )

                    # Background rectangle for text
                    cv2.rectangle(
                        annotated_image,
                        (xmin, ymin - label_h - baseline - 4),
                        (xmin + label_w, ymin),
                        color,
                        -1,
                    )
                    cv2.putText(
                        annotated_image,
                        label,
                        (xmin, ymin - baseline - 2),
                        font,
                        font_scale,
                        (255, 255, 255),
                        font_thickness,
                        cv2.LINE_AA,
                    )

        # ------------------------------------------------------------------
        # 6. Encode annotated image to base64
        # ------------------------------------------------------------------
        _, buffer = cv2.imencode(".png", annotated_image)
        annotated_base64 = base64.b64encode(buffer).decode("utf-8")

        # ------------------------------------------------------------------
        # 7. Return structured result
        # ------------------------------------------------------------------
        return {
            "status": "success",
            "detection_count": len(detections),
            "image_dimensions": {"width": img_w, "height": img_h},
            "detections": detections,
            "annotated_image_base64": annotated_base64,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "detection_count": 0,
            "image_dimensions": {"width": 0, "height": 0},
            "detections": [],
            "annotated_image_base64": "",
        }


def main():
    """CLI entry point for running inference."""
    parser = argparse.ArgumentParser(
        description="Run YOLOv8 Pneumonia Detection inference on a chest X-ray"
    )
    parser.add_argument(
        "--image",
        type=str,
        required=True,
        help="Path to the input X-ray image",
    )
    parser.add_argument(
        "--weights",
        type=str,
        default=DEFAULT_WEIGHTS,
        help=f"Path to trained model weights (default: {DEFAULT_WEIGHTS})",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold (default: 0.25)",
    )
    args = parser.parse_args()

    import json

    result = predict_pneumonia(
        image_path=args.image,
        conf_thresh=args.conf,
        weights_path=args.weights,
    )

    # Print result (truncate base64 for readability)
    display = result.copy()
    if display.get("annotated_image_base64"):
        b64_str = display["annotated_image_base64"]
        display["annotated_image_base64"] = f"{b64_str[:80]}... ({len(b64_str)} chars)"

    print(json.dumps(display, indent=2))


if __name__ == "__main__":
    main()
