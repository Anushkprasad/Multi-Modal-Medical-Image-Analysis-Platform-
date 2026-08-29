"""
train.py - YOLOv8 Training Script for RSNA Pneumonia Detection

Trains a YOLOv8s model on the converted RSNA dataset for bounding box
detection of pneumonia on chest X-rays.

Usage:
    python train.py \
        --data dataset.yaml \
        --epochs 20 \
        --imgsz 640 \
        --batch 16

Output:
    Trained model weights saved to weights/best.pt
"""

import os
import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train YOLOv8 for RSNA Pneumonia Detection"
    )
    parser.add_argument(
        "--data",
        type=str,
        default="dataset.yaml",
        help="Path to dataset.yaml (default: dataset.yaml)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8s.pt",
        help="Pretrained YOLOv8 model to fine-tune (default: yolov8s.pt)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=20,
        help="Number of training epochs (default: 20)",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Input image size (default: 640)",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=16,
        help="Batch size (default: 16)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="",
        help="Device to train on: '' for auto, '0' for GPU 0, 'cpu' for CPU",
    )
    parser.add_argument(
        "--project",
        type=str,
        default="runs/detect",
        help="Project directory for training outputs (default: runs/detect)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="pneumonia_yolov8",
        help="Experiment name (default: pneumonia_yolov8)",
    )
    return parser.parse_args()


def main():
    """Main training pipeline."""
    args = parse_args()

    # ------------------------------------------------------------------
    # 1. Validate dataset.yaml exists
    # ------------------------------------------------------------------
    if not os.path.exists(args.data):
        raise FileNotFoundError(
            f"Dataset config not found: {args.data}\n"
            "Run convert_rsna.py first to generate the dataset and dataset.yaml."
        )

    print("=" * 60)
    print("YOLOv8 Pneumonia Detection - Training")
    print("=" * 60)
    print(f"  Model       : {args.model}")
    print(f"  Dataset     : {args.data}")
    print(f"  Epochs      : {args.epochs}")
    print(f"  Image Size  : {args.imgsz}")
    print(f"  Batch Size  : {args.batch}")
    print(f"  Device      : {args.device or 'auto'}")
    print(f"  Project     : {args.project}")
    print(f"  Experiment  : {args.name}")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 2. Load pretrained YOLOv8 model
    # ------------------------------------------------------------------
    print(f"\n[INFO] Loading pretrained model: {args.model}")
    model = YOLO(args.model)

    # ------------------------------------------------------------------
    # 3. Train the model
    # ------------------------------------------------------------------
    print("[INFO] Starting training...\n")
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device if args.device else None,
        project=args.project,
        name=args.name,
        exist_ok=True,
        verbose=True,
        # Optimization settings
        optimizer="auto",
        lr0=0.01,
        lrf=0.01,
        # Data augmentation
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        flipud=0.5,
        fliplr=0.5,
        mosaic=1.0,
        # Save settings
        save=True,
        save_period=-1,  # save only final and best
    )

    # ------------------------------------------------------------------
    # 4. Copy best weights to weights/best.pt
    # ------------------------------------------------------------------
    weights_dir = Path("weights")
    weights_dir.mkdir(exist_ok=True)

    # The best weights are saved by ultralytics in the project/name directory
    train_dir = Path(args.project) / args.name / "weights"
    best_src = train_dir / "best.pt"
    best_dst = weights_dir / "best.pt"

    if best_src.exists():
        shutil.copy2(str(best_src), str(best_dst))
        print(f"\n[SUCCESS] Best weights copied to: {best_dst.resolve()}")
    else:
        # Fallback: copy last.pt if best.pt not found
        last_src = train_dir / "last.pt"
        if last_src.exists():
            shutil.copy2(str(last_src), str(best_dst))
            print(f"\n[WARNING] best.pt not found; copied last.pt to: {best_dst.resolve()}")
        else:
            print(f"\n[ERROR] No weights found in: {train_dir.resolve()}")

    # ------------------------------------------------------------------
    # 5. Print final summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"  Results directory : {(Path(args.project) / args.name).resolve()}")
    print(f"  Best weights      : {best_dst.resolve()}")
    print(f"  Metrics available in: {(Path(args.project) / args.name).resolve()}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    main()
