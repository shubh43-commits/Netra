"""
Natural Language Scene Description Generator for Netra.
Translates detected computer vision objects and proximity into natural, clear spoken phrases
in English and Hindi (Devanagari).
"""
from typing import List, Dict, Any
from .priority import select_top_hazards

# Hindi vocabulary mappings for obstacle labels
HINDI_CLASS_NAMES: Dict[str, str] = {
    "person": "व्यक्ति",
    "car": "गाड़ी",
    "motorcycle": "मोटरसाइकिल",
    "bicycle": "साइकिल",
    "bus": "बस",
    "truck": "ट्रक",
    "auto_rickshaw": "ऑटो",
    "stairs": "सीढ़ियाँ",
    "pothole": "गड्ढा",
    "open_drain": "खुला नाला",
    "curb": "फ़ुटपाथ का किनारा",
    "traffic light": "ट्रैफ़िक लाइट",
    "stop sign": "स्टॉप साइन",
    "dog": "कुत्ता",
    "cow": "गाय",
    "pole": "खंभा",
    "door": "दरवाज़ा",
    "chair": "कुर्सी",
    "bench": "बेंच",
}

# Hindi direction mappings
HINDI_DIRECTIONS: Dict[str, str] = {
    "ahead": "ठीक सामने",
    "left": "बाईं ओर",
    "right": "दाईं ओर",
}


def describe_scene(
    detections: List[Dict[str, Any]],
    language: str = "en",
    max_items: int = 2
) -> Dict[str, Any]:
    """
    Constructs a concise, speech-friendly description of the path forward.
    Returns:
    {
        "text": str,
        "items": List[Dict],
        "language": str
    }
    """
    lang = language.lower()[:2]
    if lang not in ("en", "hi"):
        lang = "en"

    # Select top prioritized hazards
    top_hazards = select_top_hazards(detections, limit=max_items)

    if not top_hazards:
        if lang == "hi":
            summary_text = "आगे रास्ता साफ़ है। कोई बाधा नहीं दिखी।"
        else:
            summary_text = "All clear ahead. No obstacles detected."

        return {
            "text": summary_text,
            "items": [],
            "language": lang,
        }

    sentences: List[str] = []

    for item in top_hazards:
        label = item.get("class_name", "object").lower()
        dist = round(float(item.get("distance_m", 3.0)), 1)
        direction = item.get("direction", "ahead")
        approaching = item.get("approaching", False)

        # Format distance string nicely (e.g., 3 instead of 3.0 if integer)
        dist_str = str(int(dist)) if dist.is_integer() else str(dist)

        if lang == "hi":
            label_hi = HINDI_CLASS_NAMES.get(label, label)
            dir_hi = HINDI_DIRECTIONS.get(direction, "सामने")

            if approaching:
                sentences.append(f"{dir_hi}, लगभग {dist_str} मीटर पर {label_hi} आ रहा है।")
            elif direction == "ahead":
                sentences.append(f"सामने, लगभग {dist_str} मीटर पर {label_hi} है।")
            else:
                sentences.append(f"आपके {dir_hi}, लगभग {dist_str} मीटर पर {label_hi} है।")
        else:
            article = "An" if label[0] in "aeiou" else "A"
            if approaching:
                sentences.append(f"An approaching {label} is {direction}, about {dist_str} metres away.")
            elif direction == "ahead":
                sentences.append(f"{article} {label} is ahead, about {dist_str} metres away.")
            else:
                sentences.append(f"{article} {label} is on your {direction}, {dist_str} metres away.")

    combined_text = " ".join(sentences)
    return {
        "text": combined_text,
        "items": top_hazards,
        "language": lang,
    }
