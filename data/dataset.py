from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

PATHOLOGY_CLASSES = [
    "Atelectasis",
    "Cardiomegaly",
    "Consolidation",
    "Edema",
    "Effusion",
    "Emphysema",
    "Fibrosis",
    "Hernia",
    "Infiltration",
    "Mass",
    "Nodule",
    "Pleural_Thickening",
    "Pneumonia",
    "Pneumothorax",
]

DEFAULT_IMAGE_SIZE = 224
DEFAULT_MEAN = (0.485, 0.456, 0.406)
DEFAULT_STD = (0.229, 0.224, 0.225)


def default_image_transform(image_size: int = DEFAULT_IMAGE_SIZE) -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.Grayscale(num_output_channels=3),
            transforms.ToTensor(),
            transforms.Normalize(mean=DEFAULT_MEAN, std=DEFAULT_STD),
        ]
    )


class ChestXrayDataset(Dataset):
    """PyTorch dataset for the NIH ChestX-ray14 sample subset."""

    def __init__(
        self,
        dataset_dir: str | Path | None = None,
        csv_name: str = "sample_labels.csv",
        transform: Optional[Callable] = None,
    ) -> None:
        base_dir = Path(dataset_dir) if dataset_dir is not None else Path(__file__).resolve().parent / "nih_chestxray14"
        self.dataset_dir = Path(base_dir)
        self.csv_path = self.dataset_dir / csv_name
        self.annotations = pd.read_csv(self.csv_path)
        self.class_names = PATHOLOGY_CLASSES
        self.class_to_index = {name: idx for idx, name in enumerate(self.class_names)}
        self.transform = transform if transform is not None else default_image_transform()

    def _resolve_image_path(self, image_name: str) -> Path:
        image_name = str(image_name).strip()
        if not image_name:
            raise FileNotFoundError("Image Index is empty.")

        candidate_dirs = [
            self.dataset_dir,
            self.dataset_dir / "images",
            self.dataset_dir / "sample",
            self.dataset_dir / "sample" / "images",
            self.dataset_dir / "sample" / "sample",
            self.dataset_dir / "sample" / "sample" / "images",
        ]

        for directory in candidate_dirs:
            candidate = directory / image_name
            if candidate.exists():
                return candidate

        matches = sorted(self.dataset_dir.rglob(image_name))
        if matches:
            return matches[0]

        raise FileNotFoundError(f"Could not locate image '{image_name}' under {self.dataset_dir}")

    def encode_labels(self, finding_labels: str | float | None) -> np.ndarray:
        label_vector = np.zeros(len(self.class_names), dtype=np.float32)
        if pd.isna(finding_labels):
            return label_vector

        text = str(finding_labels).strip()
        if not text or text.lower() == "no finding":
            return label_vector

        for label in text.split("|"):
            cleaned = label.strip()
            if not cleaned:
                continue
            if cleaned in self.class_to_index:
                label_vector[self.class_to_index[cleaned]] = 1

        return label_vector

    def __len__(self) -> int:
        return len(self.annotations)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor, str]:
        row = self.annotations.iloc[index]
        image_name = str(row["Image Index"])
        image_path = self._resolve_image_path(image_name)

        image = Image.open(image_path).convert("RGB")
        if self.transform is not None:
            image = self.transform(image)

        label_vector = torch.tensor(self.encode_labels(row["Finding Labels"]), dtype=torch.float32)
        return image, label_vector, str(image_path)

    def load_samples(self, count: int = 3) -> List[Tuple[str, np.ndarray, np.ndarray]]:
        limit = min(count, len(self.annotations))
        outputs: List[Tuple[str, np.ndarray, np.ndarray]] = []
        for i in range(limit):
            image_tensor, label_tensor, image_path = self.__getitem__(i)
            outputs.append((image_path, image_tensor.numpy(), label_tensor.numpy()))
        return outputs


def create_chestxray_loader(
    dataset_dir: str | Path | None = None,
    csv_name: str = "sample_labels.csv",
    batch_size: int = 8,
    shuffle: bool = False,
    num_workers: int = 0,
    transform: Optional[Callable] = None,
) -> DataLoader:
    dataset = ChestXrayDataset(dataset_dir=dataset_dir, csv_name=csv_name, transform=transform)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)


if __name__ == "__main__":
    dataset = ChestXrayDataset()
    for image_path, image, label_vector in dataset.load_samples(count=3):
        print(f"image path: {image_path}")
        print(f"image shape: {image.shape}")
        print(f"label vector shape: {label_vector.shape}")
        print(f"label vector: {label_vector.tolist()}")
        print("-" * 60)
