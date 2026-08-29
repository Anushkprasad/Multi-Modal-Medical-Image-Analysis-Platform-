from __future__ import annotations

import base64
import io
import struct
import sys
import zlib
from pathlib import Path

import torch
from PIL import Image
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.multimodal_service import call_multimodal
from models.gradcam import GradCAM, encode_heatmap_png_base64, find_last_conv_layer


class TinyConvClassifier(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 4, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(4, 8, kernel_size=3, padding=1),
            nn.ReLU(),
        )
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Linear(8, 2)

    def forward(self, image_tensor: torch.Tensor) -> torch.Tensor:
        features = self.features(image_tensor)
        pooled = self.pool(features).flatten(start_dim=1)
        return self.classifier(pooled)


def _make_tiny_png() -> bytes:
    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        payload = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + payload + crc

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 2, 0, 0, 0))
    row = b"\x00" + b"\xff\xff\xff" * 8
    idat = chunk(b"IDAT", zlib.compress(row * 8))
    iend = chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


def test_gradcam_generates_heatmap_for_conv_model() -> None:
    torch.manual_seed(42)
    model = TinyConvClassifier()
    model.eval()

    target_layer = find_last_conv_layer(model)
    assert target_layer is not None

    image_tensor = torch.rand(1, 3, 16, 16)
    grad_cam = GradCAM(model, target_layer)
    try:
        heatmap = grad_cam(image_tensor, target_class=1)
    finally:
        grad_cam.close()

    assert heatmap.shape == (1, 16, 16)
    assert torch.isfinite(heatmap).all()
    assert heatmap.min().item() >= 0.0
    assert heatmap.max().item() <= 1.0

    encoded = encode_heatmap_png_base64(heatmap[0])
    decoded = base64.b64decode(encoded)
    assert Image.open(io.BytesIO(decoded)).size == (16, 16)


def test_service_keeps_gradcam_uncomputed_for_placeholder_pipeline() -> None:
    response = call_multimodal(_make_tiny_png(), "Patient reports cough.")

    assert "grad_cam" in response
    assert response["grad_cam"] is None
    assert response["grad_cam_status"] == "not_computed"
    assert response["status"] == "model_unavailable"
    assert len(response["pathology_probabilities"]) == 14
    assert set(response["pathology_probabilities"].values()) == {None}


def main() -> None:
    test_gradcam_generates_heatmap_for_conv_model()
    print("Grad-CAM utility test passed.")

    test_service_keeps_gradcam_uncomputed_for_placeholder_pipeline()
    print("Service Grad-CAM availability test passed.")


if __name__ == "__main__":
    main()
