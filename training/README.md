# Netra AI - Model Training & Fine-Tuning Guide

This guide describes how to collect custom data, fine-tune YOLO models for Indian street scenarios, and export optimized models for the browser and server.

---

## 1. Custom Assistive Classes

Netra adds specific obstacle classes critical for visually impaired navigation in Indian cities:

| Class ID | Name | Why It Matters | Priority Weight |
| :--- | :--- | :--- | :--- |
| `0` | `person` | Pedestrians walking directly in path | Medium |
| `1` | `car` | Moving or parked road traffic | High |
| `2` | `auto_rickshaw` | Unpredictable lateral movement | High |
| `3` | `cow` | Common road / sidewalk obstacle | Medium |
| `4` | `stairs_up` | Ascending steps / curbs | High |
| `5` | `stairs_down` | Dangerous descent drop-offs | **Critical** |
| `6` | `pothole` | Tripping & cane obstruction hazard | **Critical** |
| `7` | `open_drain` | Severe fall hazard on footpaths | **Critical** |
| `8` | `pole` | Head and torso-height collision risk | High |
| `9` | `door` | Indoor/outdoor doorway transitions | Low |
| `10` | `traffic_light` | Pedestrian crossing safety (red/green) | High |

---

## 2. Public Dataset Sources

You can assemble a dataset using these open datasets:
1. **Roboflow Universe**:
   - [Pothole Detection Dataset](https://universe.roboflow.com/search?q=pothole) (2,000+ labeled images)
   - [Open Manholes / Drains](https://universe.roboflow.com/search?q=drain) (800+ labeled images)
   - [Indian Traffic & Auto Rickshaws](https://universe.roboflow.com/search?q=auto+rickshaw)
2. **Indian Driving Dataset (IDD)**:
   - High-density urban and rural roads in Indian cities: [idd.insaan.iiit.ac.in](http://idd.insaan.iiit.ac.in/)
3. **Open Images Dataset v7**:
   - Stairs, doors, street lights, and poles.

---

## 3. Gathering Extra Real-World Phone Photos

1. **Camera Angle**: Hold the smartphone at chest height (~1.3 meters) tilted downward 5°–10° (matching natural walking posture).
2. **Conditions**:
   - Harsh sunlight & deep shadows (noon).
   - Low light / dusk (5:30 PM–7:00 PM).
   - Rainy reflections / wet asphalt.
3. **Labeling**: Use [Roboflow](https://roboflow.com) or [CVAT](https://www.cvat.ai/) to draw tight bounding boxes.

---

## 4. Running Training

Ensure dependencies are installed:
```bash
pip install ultralytics torch torchvision pyyaml
```

Run fine-tuning:
```bash
python training/train_custom_yolo.py
```

---

## 5. Exporting for Web & ModelHub

Export trained weights to ONNX with graph simplification:
```bash
python training/export_model.py training/runs/netra_assistive_yolo/weights/best.pt
```

This generates `static/models/netra_latest.onnx` and outputs the cryptographic SHA-256 hash ready for registration in the **Netra ModelHub Admin** (`/admin/modelhub/modelversion/`).
