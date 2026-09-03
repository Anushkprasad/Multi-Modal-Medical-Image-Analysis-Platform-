import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.dataset import ChestXrayDataset, create_chestxray_loader, default_image_transform


def main() -> None:
    dataset = ChestXrayDataset(transform=default_image_transform())
    loader = create_chestxray_loader(batch_size=4, shuffle=False, transform=default_image_transform())

    batch_images, batch_labels, batch_paths = next(iter(loader))
    print(f"image tensor shape: {tuple(batch_images.shape)}")
    print(f"label tensor shape: {tuple(batch_labels.shape)}")
    print(f"number of classes: {batch_labels.shape[1]}")
    print(f"sample paths: {batch_paths[:2]}")
    print(f"sample labels: {batch_labels[:2].tolist()}")


if __name__ == "__main__":
    main()
