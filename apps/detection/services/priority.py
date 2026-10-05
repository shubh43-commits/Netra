"""
Hazard Priority Ranking Service for Netra.
Evaluates detected obstacles and ranks them by:
1. Inherent danger class (vehicles, drop-offs, stairs, potholes)
2. Closeness / distance proximity
3. Walking corridor alignment (ahead vs peripheral)
4. Active approaching velocity

Returns the top 1 or 2 most urgent hazards to avoid cognitive overload for visually impaired users.
"""
from typing import List, Dict, Any
from .constants import DANGER_CLASS_SCORES, DEFAULT_DANGER_SCORE


def calculate_hazard_score(detection: Dict[str, Any]) -> float:
    """
    Computes a composite priority score (0 to 120+) for a single detection item.
    """
    class_name = detection.get("class_name", "").lower().strip()
    distance_m = float(detection.get("distance_m", 5.0))
    direction = detection.get("direction", "ahead")
    approaching = bool(detection.get("approaching", False))
    confidence = float(detection.get("confidence", 0.5))

    # 1. Base Class Danger (0 - 100)
    base_class_score = float(DANGER_CLASS_SCORES.get(class_name, DEFAULT_DANGER_SCORE))

    # 2. Closeness Proximity Score (0 - 100)
    # Distance under 10m scales up; distance under 2m is urgent
    closeness_score = max(0.0, min(100.0, (10.0 - distance_m) * 10.0))

    # 3. Path Corridor Alignment (0 - 100)
    # Directly ahead is in direct walking path; peripheral left/right is lower
    if direction == "ahead":
        path_score = 100.0
    else:
        path_score = 45.0

    # 4. Approaching Motion Velocity (0 - 100)
    approach_score = 100.0 if approaching else 15.0

    # Composite weighted score
    composite_score = (
        (base_class_score * 0.35) +
        (closeness_score * 0.35) +
        (path_score * 0.15) +
        (approach_score * 0.15)
    )

    # Emergency proximity bonus for imminent collision hazards (< 2.0 meters)
    if distance_m <= 2.0:
        composite_score += 25.0

    # Factor in detection confidence (penalize low confidence noise)
    final_score = composite_score * max(0.4, confidence)
    return round(final_score, 2)


def select_top_hazards(detections: List[Dict[str, Any]], limit: int = 2) -> List[Dict[str, Any]]:
    """
    Ranks detections by danger priority and returns the top N hazards (default 2).
    Attaches 'priority_score' to each item.
    """
    if not detections:
        return []

    scored_items = []
    for item in detections:
        item_copy = dict(item)
        item_copy["priority_score"] = calculate_hazard_score(item_copy)
        scored_items.append(item_copy)

    # Sort descending by priority score
    scored_items.sort(key=lambda d: d["priority_score"], reverse=True)
    return scored_items[:limit]
