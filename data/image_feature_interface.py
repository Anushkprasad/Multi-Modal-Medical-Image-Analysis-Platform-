from __future__ import annotations

from abc import ABC, abstractmethod

import torch


class ImageFeatureExtractor(ABC):
    """Abstract interface for future image backbones such as DenseNet."""

    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Return image features for a batch of images."""
        raise NotImplementedError


class IdentityImageFeatureExtractor(ImageFeatureExtractor):
    """Simple placeholder extractor. This is not a DenseNet implementation."""

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x.flatten(start_dim=1)
