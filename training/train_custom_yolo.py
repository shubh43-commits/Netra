"""
Netra AI - Custom YOLO Fine-Tuning Pipeline for Indian Assistive Obstacles.

Fine-tunes lightweight YOLO models (YOLOv8n / YOLO11n) on Indian sidewalk & road hazards:
Custom classes:
0: person
1: car
2: auto_rickshaw
3: cow
4: stairs_up
5: stairs_down
6: pothole
7: open_drain
8: pole
9: door
10: traffic_light

Public Data Sources:
- Indian Driving Dataset (IDD): http://idd.insaan.iiit.ac.in/
- Roboflow Universe (Potholes, Open Drains, Indian Traffic): https://universe.roboflow.com/
- Open Images v7 (Stairs, Doors, Poles): https://storage.googleapis.com/openimages/web/index.html
"""
import os
import sys
import yaml
from pathlib import Path


def generate_dataset_config(dataset_dir: Path) -> Path:
    """Generates a data.yaml config for Ultralytics YOLO training."""
    dataset_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = dataset_dir / "data.yaml"

    config = {
        "path": str(dataset_dir.absolute()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {
            0: "person",
            1: "car",
            2: "auto_rickshaw",
            3: "cow",
            4: "stairs_up",
            5: "stairs_down",
            6: "pothole",
            7: "open_drain",
            8: "pole",
            9: "door",
            10: "traffic_light",
        }
    }

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"✓ Generated dataset configuration at: {yaml_path}")
    return yaml_path


def train_model(
    base_model: str = "yolov8n.pt",
    epochs: int = 50,
    imgsz: int = 416,
    batch: int = 16,
    dataset_yaml: Path = None,
    device: str = "0"
):
    """
    Executes fine-tuning with transfer learning using Ultralytics YOLO.
    Uses augmentations tailored for mobile smartphone cameras (perspective, blur, brightness).
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Ultralytics package not installed. Run: pip install ultralytics")
        sys.exit(1)

    print("=" * 65)
    print(f"NETRA AI - FINE-TUNING {base_model} FOR ASSISTIVE VISION")
    print("=" * 65)
    print(f"Base Weights : {base_model}")
    print(f"Image Size   : {imgsz}x{imgsz}")
    print(f"Epochs       : {epochs}")
    print(f"Batch Size   : {batch}")
    print(f"Dataset YAML : {dataset_yaml}")
    print("=" * 65)

    # Initialize model with pre-trained weights
    model = YOLO(base_model)

    # Train with domain-specific hyperparameters for assistive camera vision
    results = model.train(
        data=str(dataset_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        patience=12,
        save=True,
        save_period=10,
        workers=4,
        # Data Augmentations
        hsv_h=0.015,  # Hue variation
        hsv_s=0.7,    # Saturation variation
        hsv_v=0.4,    # Value (lighting/shadows)
        degrees=10.0, # Camera tilt
        translate=0.1,# Pan
        scale=0.3,    # Distance variation
        shear=2.0,    # Perspective skew
        flipud=0.0,   # No vertical flipping for walking orientation
        fliplr=0.5,   # Left-right mirror augmentation
        mosaic=1.0,   # Multi-image context mosaic
        mixup=0.1,    # Object blend
        project="training/runs",
        name="netra_assistive_yolo",
    )

    print("\n✓ Training completed!")
    print(f"Best weights saved at: {model.trainer.best}")

    # Evaluate validation metrics
    metrics = model.val()
    print("\nValidation Results:")
    print(f"mAP@50    : {metrics.box.map50:.4f}")
    print(f"mAP@50-95 : {metrics.box.map:.4f}")
    print(f"Precision : {metrics.box.mp:.4f}")
    print(f"Recall    : {metrics.box.mr:.4f}")

    return model.trainer.best


if __name__ == "__main__":
    dataset_path = Path("training/dataset")
    yaml_config = generate_dataset_config(dataset_path)

    # Check if dataset images exist; if not, provide instructions
    train_images = dataset_path / "images" / "train"
    if not train_images.exists() or len(list(train_images.glob("*.*"))) == 0:
        print("\n" + "!" * 65)
        print("NOTICE: No training images found in 'training/dataset/images/train/'.")
        print("To train on real images:")
        print("1. Collect 150-300 phone camera photos of sidewalks, stairs, and roads.")
        print("2. Label them in YOLO format using CVAT or Roboflow.")
        print("3. Place images in 'training/dataset/images/train' and labels in 'training/dataset/labels/train'.")
        print("4. Re-run this script to start training.")
        print("!" * 65)
    else:
        train_model(
            base_model="yolov8n.pt",
            epochs=50,
            imgsz=416,
            dataset_yaml=yaml_config,
            device="0" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
        )
