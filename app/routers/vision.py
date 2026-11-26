import base64
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.store import Store
from ..models.inventory import InventoryItem
from ..vision_service import run_vision_inference, CLASS_METADATA

router = APIRouter(prefix="/api/vision", tags=["Computer Vision"])


class VisionDetectBase64Request(BaseModel):
    image_base64: str
    confidence: Optional[float] = 0.30
    store_id: Optional[int] = 1


def attach_store_inventory_to_vision(result: dict, store_id: Optional[int], db: Session) -> dict:
    target_store_id = store_id or 1
    target_store = db.query(Store).filter(Store.id == target_store_id).first()
    store_currency = target_store.currency if target_store else "USD"
    currency_symbol = {"EUR": "€", "GBP": "£", "CAD": "C$", "USD": "$"}.get(store_currency, "$")

    result["store_id"] = target_store_id
    result["store_name"] = target_store.name if target_store else "Downtown Supermarket"
    result["store_currency"] = store_currency
    result["currency_symbol"] = currency_symbol

    inv_items = db.query(InventoryItem).filter(InventoryItem.store_id == target_store_id).all()
    inv_map = {i.class_label.lower(): i for i in inv_items}

    for item in result.get("detections", []):
        cl = item["classLabel"].replace("_rotten", "").lower()
        inv = inv_map.get(cl)
        if inv:
            item["storePrice"] = float(inv.unit_price)
            item["storeCurrency"] = store_currency
            item["currencySymbol"] = currency_symbol
            item["onHand"] = inv.on_hand
            item["stockStatus"] = inv.status
            item["unit"] = "kg" if cl in ["banana", "tomato"] else "pack" if cl in ["strawberry"] else "each"
            item["name"] = inv.name
        else:
            item["storePrice"] = 1.00
            item["storeCurrency"] = store_currency
            item["currencySymbol"] = currency_symbol
            item["onHand"] = 10
            item["stockStatus"] = "In stock"
            item["unit"] = "each"
            item["name"] = item.get("displayName") or cl.title()

    for item in result.get("summary", []):
        cl = item["classLabel"].replace("_rotten", "").lower()
        inv = inv_map.get(cl)
        if inv:
            item["storePrice"] = float(inv.unit_price)
            item["storeCurrency"] = store_currency
            item["currencySymbol"] = currency_symbol
            item["onHand"] = inv.on_hand
            item["stockStatus"] = inv.status
            item["unit"] = "kg" if cl in ["banana", "tomato"] else "pack" if cl in ["strawberry"] else "each"
            item["name"] = inv.name
        else:
            item["storePrice"] = 1.00
            item["storeCurrency"] = store_currency
            item["currencySymbol"] = currency_symbol
            item["onHand"] = 10
            item["stockStatus"] = "In stock"
            item["unit"] = "each"
            item["name"] = item.get("displayName") or cl.title()

    return result


@router.get("/classes")
def get_vision_classes():
    """
    Returns supported retail object and freshness classification labels with metadata.
    """
    return {
        "classes": list(CLASS_METADATA.keys()),
        "count": len(CLASS_METADATA),
        "metadata": CLASS_METADATA,
    }


@router.post("/detect")
async def detect_from_upload(
    file: Optional[UploadFile] = File(None),
    confidence: float = 0.30,
    store_id: Optional[int] = 1,
    db: Session = Depends(get_db),
):
    """
    Run YOLO11 object detection directly on an uploaded photo.
    Counts items across the 27 retail classes and returns bounding boxes and store pricing.
    """
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image file provided for vision detection."
        )
    image_bytes = await file.read()
    try:
        raw_result = run_vision_inference(image_bytes, conf_threshold=confidence)
        return attach_store_inventory_to_vision(raw_result, store_id, db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}"
        )


@router.post("/detect-base64")
def detect_from_base64(payload: VisionDetectBase64Request, db: Session = Depends(get_db)):
    """
    Run YOLO11 object detection on a base64 encoded snapshot (e.g. from live webcam stream).
    Attaches store-specific price, currency, and inventory levels for the active store.
    """
    try:
        raw_b64 = payload.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        image_bytes = base64.b64decode(raw_b64)
        raw_result = run_vision_inference(image_bytes, conf_threshold=payload.confidence or 0.30)
        return attach_store_inventory_to_vision(raw_result, payload.store_id, db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}"
        )
