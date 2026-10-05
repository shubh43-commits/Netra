"""
Constants, object height models, and hazard weights for Netra Computer Vision & Proximity Estimation.
"""
from typing import Dict

# Real-world estimated object heights in meters (metric)
# Used for single-camera monocular distance estimation based on bounding box height
REAL_WORLD_HEIGHTS_M: Dict[str, float] = {
    # High-danger dynamic obstacles
    "car": 1.5,
    "truck": 3.2,
    "bus": 3.2,
    "motorcycle": 1.1,
    "bicycle": 1.0,
    "auto_rickshaw": 1.8,
    "cow": 1.5,
    "horse": 1.6,

    # Pedestrians & Living entities
    "person": 1.7,
    "dog": 0.6,
    "cat": 0.3,

    # Structural / Ground Drop Hazards
    "stairs": 1.2,
    "pothole": 0.3,
    "open_drain": 0.4,
    "curb": 0.2,

    # Urban Infrastructure & Street Obstacles
    "traffic light": 1.0,
    "stop sign": 0.8,
    "fire hydrant": 0.8,
    "pole": 3.0,
    "door": 2.1,
    "bench": 0.8,
    "chair": 0.85,
    "couch": 0.85,
    "bottle": 0.25,
    "backpack": 0.45,
    "suitcase": 0.65,
}

DEFAULT_OBJECT_HEIGHT_M: float = 1.0

# Base camera vertical focal length calibration factor
DEFAULT_FOCAL_FACTOR: float = 1.0

# Horizontal field of view split for direction determination
DIRECTION_THRESHOLDS = {
    "left_limit": 0.33,
    "right_limit": 0.66,
}

# Inherent hazard danger rankings (0 to 100)
DANGER_CLASS_SCORES: Dict[str, int] = {
    "truck": 98,
    "bus": 98,
    "car": 95,
    "auto_rickshaw": 92,
    "motorcycle": 90,
    "open_drain": 92,
    "stairs": 90,
    "pothole": 88,
    "bicycle": 75,
    "cow": 75,
    "person": 70,
    "dog": 65,
    "pole": 60,
    "traffic light": 55,
    "door": 50,
    "bench": 45,
    "fire hydrant": 45,
}

DEFAULT_DANGER_SCORE: int = 40
