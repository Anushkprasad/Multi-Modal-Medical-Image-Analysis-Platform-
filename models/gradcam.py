from __future__ import annotations

import base64
from io import BytesIO
from typing import Optional

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch import nn


class GradCAM:
    """Compute Grad-CAM heatmaps for models with convolutional feature maps."""

    def __init__(self, model: nn.Module, target_layer: nn.Module) -> None:
        self.model = model
        self.target_layer = target_layer
        self.activations: Optional[torch.Tensor] = None
        self.gradients: Optional[torch.Tensor] = None
        self._forward_handle = target_layer.register_forward_hook(self._save_activations)
        self._backward_handle = target_layer.register_full_backward_hook(self._save_gradients)

    def _save_activations(self, _module: nn.Module, _inputs: tuple, output: torch.Tensor) -> None:
        self.activations = output

    def _save_gradients(
        self,
        _module: nn.Module,
        _grad_input: tuple,
        grad_output: tuple[torch.Tensor, ...],
    ) -> None:
        self.gradients = grad_output[0]

    def close(self) -> None:
        self._forward_handle.remove()
        self._backward_handle.remove()

    def __call__(self, inputs: torch.Tensor, target_class: Optional[int] = None) -> torch.Tensor:
        self.model.zero_grad(set_to_none=True)
        self.activations = None
        self.gradients = None

        logits = self.model(inputs)
        if logits.ndim != 2:
            raise ValueError(f"Expected 2D logits of shape [batch, classes], got {tuple(logits.shape)}.")

        if target_class is None:
            target_scores = logits.max(dim=1).values
        else:
            target_scores = logits[:, target_class]

        target_scores.sum().backward()

        if self.activations is None or self.gradients is None:
            raise RuntimeError("Grad-CAM hooks did not capture activations and gradients.")
        if self.activations.ndim != 4 or self.gradients.ndim != 4:
            raise ValueError("Grad-CAM requires 4D convolutional activations and gradients.")

        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        heatmap = torch.relu((weights * self.activations).sum(dim=1, keepdim=True))
        heatmap = F.interpolate(
            heatmap,
            size=inputs.shape[-2:],
            mode="bilinear",
            align_corners=False,
        )
        heatmap = heatmap.squeeze(1)

        batch_min = heatmap.flatten(1).min(dim=1).values[:, None, None]
        batch_max = heatmap.flatten(1).max(dim=1).values[:, None, None]
        return (heatmap - batch_min) / (batch_max - batch_min + 1e-8)


def find_last_conv_layer(model: nn.Module) -> Optional[nn.Module]:
    last_conv: Optional[nn.Module] = None
    for module in model.modules():
        if isinstance(module, nn.Conv2d):
            last_conv = module
    return last_conv


def encode_heatmap_png_base64(heatmap: torch.Tensor) -> str:
    heatmap_array = heatmap.detach().cpu().clamp(0, 1).numpy()
    heatmap_uint8 = (heatmap_array * 255).astype(np.uint8)

    image = Image.fromarray(heatmap_uint8, mode="L")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
