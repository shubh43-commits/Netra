"""
Lightweight real-time IoU object tracker for camera streams.
Determines whether obstacles are actively approaching the user on a per-connection basis.
"""
import time
from typing import List, Dict, Any, Optional


def compute_iou(box1: List[float], box2: List[float]) -> float:
    """
    Computes Intersection-over-Union between two boxes [x, y, w, h] (normalized 0-1).
    """
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    # Coordinates of intersection rectangle
    ix1 = max(x1, x2)
    iy1 = max(y1, y2)
    ix2 = min(x1 + w1, x2 + w2)
    iy2 = min(y1 + h1, y2 + h2)

    inter_w = max(0.0, ix2 - ix1)
    inter_h = max(0.0, iy2 - iy1)
    inter_area = inter_w * inter_h

    area1 = w1 * h1
    area2 = w2 * h2
    union_area = area1 + area2 - inter_area

    if union_area <= 0:
        return 0.0

    return inter_area / union_area


class ObjectTrack:
    """
    Tracks an individual detected object across sequential video frames.
    """
    def __init__(self, track_id: int, label: str, box: List[float], distance_m: float):
        self.track_id = track_id
        self.label = label
        self.box = box
        self.area = box[2] * box[3]
        self.distance_m = distance_m
        self.last_seen = time.time()
        self.history_distances: List[float] = [distance_m]
        self.history_areas: List[float] = [self.area]
        self.approaching = False

    def update(self, box: List[float], distance_m: float) -> None:
        self.box = box
        current_area = box[2] * box[3]
        self.area = current_area
        self.distance_m = distance_m
        self.last_seen = time.time()

        self.history_distances.append(distance_m)
        self.history_areas.append(current_area)

        # Keep last 5 samples
        if len(self.history_distances) > 5:
            self.history_distances.pop(0)
            self.history_areas.pop(0)

        # Evaluate approach condition:
        # Distance is decreasing OR bounding box area is expanding
        if len(self.history_distances) >= 2:
            delta_dist = self.history_distances[-1] - self.history_distances[0]
            delta_area = (self.history_areas[-1] - self.history_areas[0]) / max(1e-5, self.history_areas[0])

            # Approaching if distance decreased by >= 0.15m or area expanded by >= 8%
            self.approaching = (delta_dist < -0.15) or (delta_area > 0.08)


class StreamTracker:
    """
    Session-level object tracker instantiated per active WebSocket connection or stream.
    """
    def __init__(self, iou_threshold: float = 0.25, max_age_seconds: float = 1.5):
        self.iou_threshold = iou_threshold
        self.max_age_seconds = max_age_seconds
        self.tracks: Dict[int, ObjectTrack] = {}
        self.next_id = 1

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes raw detections and annotates each with:
        - track_id: int
        - approaching: bool
        """
        now = time.time()

        # 1. Clean expired tracks
        self.tracks = {
            tid: track for tid, track in self.tracks.items()
            if (now - track.last_seen) < self.max_age_seconds
        }

        matched_tracks = set()

        # 2. Match current detections with existing tracks
        for det in detections:
            box = det["box"]
            label = det["class_name"]
            distance = det["distance_m"]

            best_iou = 0.0
            best_track_id: Optional[int] = None

            for tid, track in self.tracks.items():
                if tid in matched_tracks or track.label != label:
                    continue
                iou = compute_iou(box, track.box)
                if iou > best_iou and iou >= self.iou_threshold:
                    best_iou = iou
                    best_track_id = tid

            if best_track_id is not None:
                track = self.tracks[best_track_id]
                track.update(box, distance)
                matched_tracks.add(best_track_id)
                det["track_id"] = track.track_id
                det["approaching"] = track.approaching
            else:
                # Initialize new track
                new_track = ObjectTrack(self.next_id, label, box, distance)
                self.tracks[self.next_id] = new_track
                matched_tracks.add(self.next_id)
                det["track_id"] = self.next_id
                det["approaching"] = False
                self.next_id += 1

        return detections
