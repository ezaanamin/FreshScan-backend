import os
import io
from typing import Dict, List, Any, Optional
from PIL import Image

def resolve_model_path() -> str:
    """
    Search multiple candidate locations for best.pt weights:
    1. MODEL_PATH environment variable (if explicitly set and file exists)
    2. /app/best_model/best.pt (inside standard Docker container)
    3. Relative to backend/ root: backend/best_model/best.pt
    4. Relative to monorepo root: best_model/best.pt
    5. Fallback to /best_model/best.pt
    """
    env_path = os.getenv("MODEL_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    candidates = [
        env_path,
        "/app/best_model/best.pt",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "best_model", "best.pt")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "best_model", "best.pt")),
        "/best_model/best.pt",
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate

    # If none found, return env_path or standard default for clear error reporting
    return env_path or "/app/best_model/best.pt"


MODEL_PATH = resolve_model_path()

# 27 Classes metadata matching multiclass_detect_stratified.yaml
CLASS_METADATA: Dict[str, Dict[str, Any]] = {
    "apple": {"singular": "Apple", "plural": "Apples", "category": "Produce", "isRotten": False, "baseFreshness": 97},
    "apple_rotten": {"singular": "Rotten Apple", "plural": "Rotten Apples", "category": "Spoilage Risk", "isRotten": True, "baseFreshness": 15},
    "banana": {"singular": "Banana", "plural": "Bananas", "category": "Produce", "isRotten": False, "baseFreshness": 95},
    "banana_rotten": {"singular": "Rotten Banana", "plural": "Rotten Bananas", "category": "Spoilage Risk", "isRotten": True, "baseFreshness": 20},
    "bolt": {"singular": "Bolt", "plural": "Bolts", "category": "Hardware & Non-Food", "isRotten": False, "baseFreshness": 100},
    "butter": {"singular": "Butter", "plural": "Butter", "category": "Dairy & Eggs", "isRotten": False, "baseFreshness": 98},
    "capsicum": {"singular": "Capsicum", "plural": "Capsicums", "category": "Produce", "isRotten": False, "baseFreshness": 94},
    "capsicum_rotten": {"singular": "Rotten Capsicum", "plural": "Rotten Capsicums", "category": "Spoilage Risk", "isRotten": True, "baseFreshness": 12},
    "eggs": {"singular": "Egg", "plural": "Eggs", "category": "Dairy & Eggs", "isRotten": False, "baseFreshness": 99},
    "garlic": {"singular": "Garlic", "plural": "Garlic", "category": "Produce", "isRotten": False, "baseFreshness": 96},
    "guava": {"singular": "Guava", "plural": "Guavas", "category": "Produce", "isRotten": False, "baseFreshness": 95},
    "guava_rotten": {"singular": "Rotten Guava", "plural": "Rotten Guavas", "category": "Spoilage Risk", "isRotten": True, "baseFreshness": 10},
    "lemon": {"singular": "Lemon", "plural": "Lemons", "category": "Produce", "isRotten": False, "baseFreshness": 96},
    "mango": {"singular": "Mango", "plural": "Mangoes", "category": "Produce", "isRotten": False, "baseFreshness": 93},
    "mango_rotten": {"singular": "Rotten Mango", "plural": "Rotten Mangoes", "category": "Spoilage Risk", "isRotten": True, "baseFreshness": 14},
    "nut": {"singular": "Nut", "plural": "Nuts", "category": "Hardware & Non-Food", "isRotten": False, "baseFreshness": 100},
    "onion": {"singular": "Onion", "plural": "Onions", "category": "Produce", "isRotten": False, "baseFreshness": 96},
    "orange": {"singular": "Orange", "plural": "Oranges", "category": "Produce", "isRotten": False, "baseFreshness": 95},
    "orange_rotten": {"singular": "Rotten Orange", "plural": "Rotten Oranges", "category": "Spoilage Risk", "isRotten": True, "baseFreshness": 15},
    "package": {"singular": "Package", "plural": "Packages", "category": "Packaging & General", "isRotten": False, "baseFreshness": 100},
    "pomegranate": {"singular": "Pomegranate", "plural": "Pomegranates", "category": "Produce", "isRotten": False, "baseFreshness": 97},
    "pomegranate_rotten": {"singular": "Rotten Pomegranate", "plural": "Rotten Pomegranates", "category": "Spoilage Risk", "isRotten": True, "baseFreshness": 18},
    "potato": {"singular": "Potato", "plural": "Potatoes", "category": "Produce", "isRotten": False, "baseFreshness": 94},
    "strawberry": {"singular": "Strawberry", "plural": "Strawberries", "category": "Produce", "isRotten": False, "baseFreshness": 92},
    "strawberry_rotten": {"singular": "Rotten Strawberry", "plural": "Rotten Strawberries", "category": "Spoilage Risk", "isRotten": True, "baseFreshness": 8},
    "tomato": {"singular": "Tomato", "plural": "Tomatoes", "category": "Produce", "isRotten": False, "baseFreshness": 95},
    "tomato_rotten": {"singular": "Rotten Tomato", "plural": "Rotten Tomatoes", "category": "Spoilage Risk", "isRotten": True, "baseFreshness": 14},
}

_yolo_model = None

def get_model():
    """Lazy load YOLO model to optimize startup time."""
    global _yolo_model
    if _yolo_model is None:
        model_path = resolve_model_path()
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model weights not found at: {model_path}")
        from ultralytics import YOLO
        _yolo_model = YOLO(model_path)
    return _yolo_model


def run_vision_inference(image_bytes: bytes, conf_threshold: float = 0.30) -> Dict[str, Any]:
    """
    Run YOLO11 object detection on image bytes.
    Counts items, computes bounding boxes (in normalized 0-100% coords),
    and assesses freshness / spoilage risk.
    """
    model = get_model()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    width, height = image.size

    # Run inference
    results = model.predict(source=image, conf=conf_threshold, iou=0.45, verbose=False)
    
    individual_detections: List[Dict[str, Any]] = []
    class_counts: Dict[str, Dict[str, Any]] = {}

    if len(results) > 0 and results[0].boxes is not None:
        boxes = results[0].boxes
        for box in boxes:
            cls_id = int(box.cls[0].item())
            class_label = model.names.get(cls_id, f"class_{cls_id}")
            confidence = round(float(box.conf[0].item()) * 100, 1)

            # Bounding box in percentage
            coords = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
            x1, y1, x2, y2 = coords
            
            box_pct = {
                "x": round(max(0.0, min(100.0, (x1 / width) * 100)), 1),
                "y": round(max(0.0, min(100.0, (y1 / height) * 100)), 1),
                "width": round(max(1.0, min(100.0, ((x2 - x1) / width) * 100)), 1),
                "height": round(max(1.0, min(100.0, ((y2 - y1) / height) * 100)), 1),
            }

            meta = CLASS_METADATA.get(class_label, {
                "singular": class_label.replace("_", " ").title(),
                "plural": class_label.replace("_", " ").title() + "s",
                "category": "Produce" if "rotten" not in class_label else "Spoilage Risk",
                "isRotten": "_rotten" in class_label,
                "baseFreshness": 15 if "_rotten" in class_label else 95,
            })

            is_rotten = meta["isRotten"]
            # Dynamic freshness calculation from confidence & baseline
            if is_rotten:
                freshness = max(5, round(meta["baseFreshness"] - (confidence * 0.05)))
            else:
                freshness = min(99, round(meta["baseFreshness"] + (confidence * 0.03)))

            detection_item = {
                "classLabel": class_label,
                "displayName": meta["singular"],
                "category": meta["category"],
                "count": 1,
                "freshness": freshness,
                "isRotten": is_rotten,
                "confidence": confidence,
                "box": box_pct,
            }
            individual_detections.append(detection_item)

            # Aggregate count per class
            if class_label not in class_counts:
                class_counts[class_label] = {
                    "classLabel": class_label,
                    "singular": meta["singular"],
                    "plural": meta["plural"],
                    "category": meta["category"],
                    "count": 0,
                    "freshness": freshness,
                    "isRotten": is_rotten,
                    "confidence": confidence,
                    "confidences": [],
                    # Representative box
                    "box": box_pct,
                }
            class_counts[class_label]["count"] += 1
            class_counts[class_label]["confidences"].append(confidence)

    # Average confidence and descriptive item count display for summary
    summary_list: List[Dict[str, Any]] = []
    for cl, data in class_counts.items():
        avg_conf = round(sum(data["confidences"]) / len(data["confidences"]), 1)
        data["confidence"] = avg_conf
        del data["confidences"]
        cnt = data["count"]
        item_word = data["plural"] if cnt > 1 else data["singular"]
        data["countDescription"] = f"{cnt} {item_word}"
        data["displayName"] = data["singular"]
        summary_list.append(data)

    total_count = len(individual_detections)
    rotten_count = sum(1 for d in individual_detections if d["isRotten"])
    fresh_count = total_count - rotten_count

    return {
        "totalCount": total_count,
        "freshCount": fresh_count,
        "rottenCount": rotten_count,
        "summary": summary_list,
        "detections": individual_detections,
    }
