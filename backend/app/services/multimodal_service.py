from __future__ import annotations

import ast
import sys
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import torch
from PIL import Image
from torch import nn
from transformers import AutoModel, AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.dataset import PATHOLOGY_CLASSES, default_image_transform
from data.image_feature_interface import IdentityImageFeatureExtractor
from models.fusion import MultiModalFusion
from models.gradcam import GradCAM, encode_heatmap_png_base64, find_last_conv_layer


DEFAULT_CLINICALBERT_MODEL = "emilyalsentzer/Bio_ClinicalBERT"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "outputs" / "member3_multimodal_model.pt"
DEFAULT_NOTE = "Chest X-ray study."
MAX_TEXT_LENGTH = 128
FLATTENED_IMAGE_DIM = 3 * 224 * 224

_MODEL_CACHE: Optional[dict[str, Any]] = None


def _empty_probabilities() -> dict[str, None]:
    return {class_name: None for class_name in PATHOLOGY_CLASSES}


def _load_clinicalbert_model_name() -> str:
    clinicalbert_path = PROJECT_ROOT / "models" / "clinicalbert.py"
    if not clinicalbert_path.exists():
        return DEFAULT_CLINICALBERT_MODEL

    tree = ast.parse(clinicalbert_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            target_names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if "MODEL_NAME" in target_names and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str):
                    return node.value.value

    return DEFAULT_CLINICALBERT_MODEL


def _torch_load(path: Path, device: torch.device) -> dict[str, Any]:
    try:
        checkpoint = torch.load(path, map_location=device, weights_only=False)
    except TypeError:
        checkpoint = torch.load(path, map_location=device)

    if not isinstance(checkpoint, dict):
        raise ValueError(f"Expected checkpoint dict at {path}, got {type(checkpoint).__name__}.")
    return checkpoint


def _infer_image_dim(checkpoint: dict[str, Any], text_dim: int) -> int:
    image_dim = checkpoint.get("image_dim")
    if isinstance(image_dim, int):
        return image_dim

    state_dict = checkpoint.get("fusion_state_dict", checkpoint)
    first_layer = state_dict.get("classifier.0.weight") if isinstance(state_dict, dict) else None
    if isinstance(first_layer, torch.Tensor) and first_layer.ndim == 2:
        return int(first_layer.shape[1] - text_dim)

    return 1024


def _checkpoint_research_only_reason(checkpoint: dict[str, Any]) -> Optional[str]:
    config = checkpoint.get("config")
    reasons: list[str] = []

    if not isinstance(checkpoint.get("fusion_state_dict"), dict):
        reasons.append("missing fusion model weights")

    if not isinstance(config, dict):
        reasons.append("missing training config metadata")
    else:
        if config.get("csv_name") == "sample_labels.csv":
            reasons.append("trained on the sample label file")
        if not config.get("text_column"):
            reasons.append("trained without a clinical-notes text column")
        if config.get("default_note") == DEFAULT_NOTE:
            reasons.append("used the same default note for text input")

    if checkpoint.get("clinicalbert_state_dict") is None:
        reasons.append("ClinicalBERT was not fine-tuned in this checkpoint")

    if checkpoint.get("image_dim") == FLATTENED_IMAGE_DIM:
        reasons.append("uses flattened pixels from the placeholder image extractor")

    best_val_loss = checkpoint.get("best_val_loss")
    if not isinstance(best_val_loss, float) or not torch.isfinite(torch.tensor(best_val_loss)):
        reasons.append("missing finite validation loss")

    if reasons:
        return (
            "Checkpoint is research-only and not suitable for prediction: "
            + "; ".join(reasons)
            + "."
        )

    return None


def _load_components() -> dict[str, Any]:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    if not DEFAULT_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained multimodal checkpoint not found at {DEFAULT_MODEL_PATH}. "
            "Inference is disabled so untrained outputs are not presented as medical predictions."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = _torch_load(DEFAULT_MODEL_PATH, device)
    research_only_reason = _checkpoint_research_only_reason(checkpoint)
    if research_only_reason:
        raise ValueError(
            f"{research_only_reason} Inference is disabled so outputs are not presented as medical predictions."
        )

    clinicalbert_name = checkpoint.get("clinicalbert_model") or _load_clinicalbert_model_name()

    tokenizer = AutoTokenizer.from_pretrained(clinicalbert_name)
    clinicalbert = AutoModel.from_pretrained(clinicalbert_name).to(device)
    clinicalbert_state_dict = checkpoint.get("clinicalbert_state_dict")
    if clinicalbert_state_dict:
        clinicalbert.load_state_dict(clinicalbert_state_dict)
    clinicalbert.eval()

    for parameter in clinicalbert.parameters():
        parameter.requires_grad = False

    text_dim = int(checkpoint.get("text_dim", clinicalbert.config.hidden_size))
    image_dim = _infer_image_dim(checkpoint, text_dim)
    fusion_model = MultiModalFusion(
        image_dim=image_dim,
        text_dim=text_dim,
        num_classes=len(PATHOLOGY_CLASSES),
    ).to(device)

    fusion_state_dict = checkpoint.get("fusion_state_dict")
    if not fusion_state_dict:
        raise ValueError(
            f"Checkpoint at {DEFAULT_MODEL_PATH} does not contain a fusion_state_dict. "
            "Inference is disabled so untrained outputs are not presented as medical predictions."
        )
    fusion_model.load_state_dict(fusion_state_dict)
    fusion_model.eval()

    _MODEL_CACHE = {
        "device": device,
        "tokenizer": tokenizer,
        "clinicalbert": clinicalbert,
        "image_transform": default_image_transform(),
        "image_extractor": IdentityImageFeatureExtractor(),
        "fusion_model": fusion_model,
        "image_dim": image_dim,
    }
    return _MODEL_CACHE


def _preprocess_image(image_bytes: bytes, components: dict[str, Any]) -> torch.Tensor:
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image_tensor = components["image_transform"](image)
    return image_tensor.unsqueeze(0).to(components["device"])


def _encode_clinical_notes(clinical_notes: Optional[str], components: dict[str, Any]) -> torch.Tensor:
    text = clinical_notes.strip() if clinical_notes and clinical_notes.strip() else DEFAULT_NOTE
    tokens = components["tokenizer"](
        [text],
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=MAX_TEXT_LENGTH,
    )
    tokens = {key: value.to(components["device"]) for key, value in tokens.items()}
    outputs = components["clinicalbert"](**tokens)
    return outputs.last_hidden_state[:, 0, :]


class _ImageOnlyMultimodalWrapper(nn.Module):
    def __init__(
        self,
        image_extractor: nn.Module,
        fusion_model: MultiModalFusion,
        text_features: torch.Tensor,
    ) -> None:
        super().__init__()
        self.image_extractor = image_extractor
        self.fusion_model = fusion_model
        self.text_features = text_features

    def forward(self, image_tensor: torch.Tensor) -> torch.Tensor:
        image_features = self.image_extractor(image_tensor)
        text_features = self.text_features.expand(image_tensor.shape[0], -1)
        return self.fusion_model(image_features, text_features)


def _compute_grad_cam(
    image_tensor: torch.Tensor,
    text_features: torch.Tensor,
    target_class: int,
    components: dict[str, Any],
) -> tuple[Optional[str], str]:
    image_extractor = components["image_extractor"]
    if not isinstance(image_extractor, nn.Module):
        return None, "unavailable: image extractor is not a torch.nn.Module"

    target_layer = find_last_conv_layer(image_extractor)
    if target_layer is None:
        return None, "unavailable: image extractor has no Conv2d layer for Grad-CAM"

    wrapper = _ImageOnlyMultimodalWrapper(
        image_extractor=image_extractor,
        fusion_model=components["fusion_model"],
        text_features=text_features.detach(),
    ).to(components["device"])
    wrapper.eval()

    grad_cam = GradCAM(wrapper, target_layer)
    try:
        with torch.enable_grad():
            heatmap = grad_cam(image_tensor.detach().requires_grad_(True), target_class=target_class)
        return encode_heatmap_png_base64(heatmap[0]), "ok"
    finally:
        grad_cam.close()


def call_multimodal(image_bytes: bytes, clinical_notes: Optional[str]) -> dict:
    try:
        components = _load_components()
        with torch.no_grad():
            image_tensor = _preprocess_image(image_bytes, components)
            image_features = components["image_extractor"].forward(image_tensor)
            if image_features.shape[1] != components["image_dim"]:
                raise ValueError(
                    f"Image feature dimension mismatch: expected {components['image_dim']}, "
                    f"got {image_features.shape[1]}."
                )

            text_features = _encode_clinical_notes(clinical_notes, components)
            logits = components["fusion_model"](image_features, text_features)
            probabilities = torch.sigmoid(logits).squeeze(0).detach().cpu().tolist()
            target_class = int(torch.argmax(logits, dim=1).item())

        grad_cam, grad_cam_status = _compute_grad_cam(
            image_tensor=image_tensor,
            text_features=text_features,
            target_class=target_class,
            components=components,
        )

        return {
            "pathology_probabilities": {
                class_name: float(probability)
                for class_name, probability in zip(PATHOLOGY_CLASSES, probabilities)
            },
            "grad_cam": grad_cam,
            "grad_cam_status": grad_cam_status,
            "status": "ok",
            "warning": "Research output only. This model has not been clinically validated for medical diagnosis.",
        }
    except Exception as exc:
        return {
            "pathology_probabilities": _empty_probabilities(),
            "grad_cam": None,
            "grad_cam_status": "not_computed",
            "status": "model_unavailable",
            "error": str(exc),
            "warning": "No medical prediction was produced.",
        }
