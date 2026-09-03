from __future__ import annotations

import argparse
import ast
import random
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, random_split
from transformers import AutoModel, AutoTokenizer

from data.dataset import ChestXrayDataset, PATHOLOGY_CLASSES, default_image_transform
from data.image_feature_interface import IdentityImageFeatureExtractor
from models.fusion import MultiModalFusion


ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET_DIR = ROOT / "data" / "nih_chestxray14"
DEFAULT_OUTPUT_DIR = ROOT / "outputs"
DEFAULT_MODEL_PATH = DEFAULT_OUTPUT_DIR / "member3_multimodal_model.pt"
DEFAULT_NOTE = "Chest X-ray study."
DEFAULT_CLINICALBERT_MODEL = "emilyalsentzer/Bio_ClinicalBERT"


class ChestXrayTextDataset(Dataset):
    """Adds clinical-note text to the existing image and label dataset."""

    def __init__(
        self,
        base_dataset: ChestXrayDataset,
        text_column: Optional[str] = None,
        default_note: str = DEFAULT_NOTE,
    ) -> None:
        self.base_dataset = base_dataset
        self.text_column = text_column
        self.default_note = default_note

        if text_column and text_column not in base_dataset.annotations.columns:
            raise ValueError(
                f"Text column '{text_column}' was not found in {base_dataset.csv_path}. "
                f"Available columns: {', '.join(base_dataset.annotations.columns)}"
            )

    def __len__(self) -> int:
        return len(self.base_dataset)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor, str, str]:
        image, labels, image_path = self.base_dataset[index]
        text = self.default_note

        if self.text_column:
            value = self.base_dataset.annotations.iloc[index][self.text_column]
            if not pd.isna(value) and str(value).strip():
                text = str(value).strip()

        return image, labels, text, image_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the Member 3 multimodal 14-label classifier.")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--csv-name", type=str, default="sample_labels.csv")
    parser.add_argument("--output-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--text-column", type=str, default=None)
    parser.add_argument("--default-note", type=str, default=DEFAULT_NOTE)
    parser.add_argument("--clinicalbert-model", type=str, default=None)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--val-split", type=float, default=0.2)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fine-tune-clinicalbert", action="store_true")
    return parser.parse_args()


def load_clinicalbert_model_name() -> str:
    clinicalbert_path = ROOT / "models" / "clinicalbert.py"
    if not clinicalbert_path.exists():
        return DEFAULT_CLINICALBERT_MODEL

    tree = ast.parse(clinicalbert_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if "MODEL_NAME" in names and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str):
                    return node.value.value

    return DEFAULT_CLINICALBERT_MODEL


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def split_dataset(dataset: Dataset, val_split: float, seed: int) -> tuple[Dataset, Dataset]:
    if not 0 < val_split < 1:
        raise ValueError("--val-split must be between 0 and 1.")

    val_size = max(1, int(len(dataset) * val_split))
    train_size = len(dataset) - val_size
    if train_size < 1:
        raise ValueError("Dataset is too small for the requested validation split.")

    generator = torch.Generator().manual_seed(seed)
    return random_split(dataset, [train_size, val_size], generator=generator)


def encode_text_batch(
    texts: Iterable[str],
    tokenizer: AutoTokenizer,
    clinicalbert: AutoModel,
    device: torch.device,
    max_length: int,
    freeze_clinicalbert: bool,
) -> torch.Tensor:
    tokens = tokenizer(
        list(texts),
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_length,
    )
    tokens = {key: value.to(device) for key, value in tokens.items()}

    if freeze_clinicalbert:
        with torch.no_grad():
            outputs = clinicalbert(**tokens)
    else:
        outputs = clinicalbert(**tokens)

    return outputs.last_hidden_state[:, 0, :]


def get_image_feature_dim(
    image_extractor: IdentityImageFeatureExtractor,
    dataset: Dataset,
    device: torch.device,
) -> int:
    image, _, _, _ = dataset[0]
    with torch.no_grad():
        features = image_extractor.forward(image.unsqueeze(0).to(device))
    return features.shape[1]


def run_epoch(
    loader: DataLoader,
    image_extractor: IdentityImageFeatureExtractor,
    tokenizer: AutoTokenizer,
    clinicalbert: AutoModel,
    fusion_model: MultiModalFusion,
    criterion: nn.Module,
    device: torch.device,
    max_length: int,
    freeze_clinicalbert: bool,
    optimizer: Optional[torch.optim.Optimizer] = None,
) -> tuple[float, float]:
    is_training = optimizer is not None
    fusion_model.train(is_training)
    clinicalbert.train(is_training and not freeze_clinicalbert)

    total_loss = 0.0
    total_labels = 0
    correct_labels = 0

    for images, labels, texts, _ in loader:
        images = images.to(device)
        labels = labels.to(device)

        if is_training:
            optimizer.zero_grad(set_to_none=True)

        image_features = image_extractor.forward(images)
        text_features = encode_text_batch(
            texts=texts,
            tokenizer=tokenizer,
            clinicalbert=clinicalbert,
            device=device,
            max_length=max_length,
            freeze_clinicalbert=freeze_clinicalbert,
        )
        logits = fusion_model(image_features, text_features)
        loss = criterion(logits, labels)

        if is_training:
            loss.backward()
            optimizer.step()

        total_loss += loss.item() * images.size(0)
        predictions = (torch.sigmoid(logits) >= 0.5).float()
        correct_labels += (predictions == labels).sum().item()
        total_labels += labels.numel()

    average_loss = total_loss / len(loader.dataset)
    label_accuracy = correct_labels / total_labels if total_labels else 0.0
    return average_loss, label_accuracy


def train() -> None:
    args = parse_args()
    set_seed(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    clinicalbert_name = args.clinicalbert_model or load_clinicalbert_model_name()

    base_dataset = ChestXrayDataset(
        dataset_dir=args.dataset_dir,
        csv_name=args.csv_name,
        transform=default_image_transform(),
    )
    dataset = ChestXrayTextDataset(
        base_dataset=base_dataset,
        text_column=args.text_column,
        default_note=args.default_note,
    )
    train_dataset, val_dataset = split_dataset(dataset, args.val_split, args.seed)

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
    )

    tokenizer = AutoTokenizer.from_pretrained(clinicalbert_name)
    clinicalbert = AutoModel.from_pretrained(clinicalbert_name).to(device)
    freeze_clinicalbert = not args.fine_tune_clinicalbert
    if freeze_clinicalbert:
        for parameter in clinicalbert.parameters():
            parameter.requires_grad = False

    image_extractor = IdentityImageFeatureExtractor()
    image_dim = get_image_feature_dim(image_extractor, dataset, device)
    text_dim = clinicalbert.config.hidden_size
    fusion_model = MultiModalFusion(
        image_dim=image_dim,
        text_dim=text_dim,
        num_classes=len(PATHOLOGY_CLASSES),
    ).to(device)

    trainable_parameters = list(fusion_model.parameters())
    if not freeze_clinicalbert:
        trainable_parameters.extend(parameter for parameter in clinicalbert.parameters() if parameter.requires_grad)

    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(trainable_parameters, lr=args.lr, weight_decay=args.weight_decay)

    best_val_loss = float("inf")
    args.output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Device: {device}")
    print(f"ClinicalBERT: {clinicalbert_name}")
    print(f"Train samples: {len(train_dataset)} | Validation samples: {len(val_dataset)}")
    print(f"Image feature dim: {image_dim} | Text feature dim: {text_dim}")

    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = run_epoch(
            loader=train_loader,
            image_extractor=image_extractor,
            tokenizer=tokenizer,
            clinicalbert=clinicalbert,
            fusion_model=fusion_model,
            criterion=criterion,
            device=device,
            max_length=args.max_length,
            freeze_clinicalbert=freeze_clinicalbert,
            optimizer=optimizer,
        )

        with torch.no_grad():
            val_loss, val_acc = run_epoch(
                loader=val_loader,
                image_extractor=image_extractor,
                tokenizer=tokenizer,
                clinicalbert=clinicalbert,
                fusion_model=fusion_model,
                criterion=criterion,
                device=device,
                max_length=args.max_length,
                freeze_clinicalbert=True,
            )

        print(
            f"Epoch {epoch}/{args.epochs} "
            f"| train_loss={train_loss:.4f} train_label_acc={train_acc:.4f} "
            f"| val_loss={val_loss:.4f} val_label_acc={val_acc:.4f}"
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(
                {
                    "fusion_state_dict": fusion_model.state_dict(),
                    "clinicalbert_state_dict": (
                        clinicalbert.state_dict() if args.fine_tune_clinicalbert else None
                    ),
                    "clinicalbert_model": clinicalbert_name,
                    "class_names": PATHOLOGY_CLASSES,
                    "image_dim": image_dim,
                    "text_dim": text_dim,
                    "threshold": 0.5,
                    "config": vars(args),
                    "best_val_loss": best_val_loss,
                },
                args.output_path,
            )
            print(f"Saved best model to {args.output_path}")


if __name__ == "__main__":
    train()
