import secrets
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.inventory import InventoryItem
from ..models.store import Store
from ..schemas.inventory import (
    InventoryCreate,
    InventoryUpdate,
    InventoryBatchScanRequest,
)
from ..vision_service import CLASS_METADATA


def get_inventory(
    db: Session,
    store_id: Optional[int] = None,
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
    spoilage_only: Optional[bool] = None,
    search: Optional[str] = None,
) -> List[InventoryItem]:
    query = db.query(InventoryItem)
    if store_id is not None:
        query = query.filter(InventoryItem.store_id == store_id)
    if category and category.lower() != 'all':
        query = query.filter(InventoryItem.category.ilike(f"%{category}%"))
    if status_filter and status_filter.lower() != 'all':
        query = query.filter(InventoryItem.status.ilike(f"%{status_filter}%"))
    if spoilage_only is not None:
        query = query.filter(InventoryItem.is_spoilage_risk == spoilage_only)
    if search:
        query = query.filter(
            (InventoryItem.name.ilike(f"%{search}%")) |
            (InventoryItem.sku.ilike(f"%{search}%")) |
            (InventoryItem.class_label.ilike(f"%{search}%"))
        )
    return query.order_by(InventoryItem.id).all()


def get_inventory_item(db: Session, item_id: int) -> InventoryItem:
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item with id {item_id} not found."
        )
    return item


def create_inventory_item(db: Session, item_in: InventoryCreate) -> InventoryItem:
    target_store_id = item_in.store_id if item_in.store_id else 1
    existing = db.query(InventoryItem).filter(
        InventoryItem.store_id == target_store_id,
        (InventoryItem.sku == item_in.sku) | (InventoryItem.class_label == item_in.class_label)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item with this SKU or class label already exists in this store."
        )
    db_item = InventoryItem(**item_in.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_inventory_item(db: Session, item_id: int, item_in: InventoryUpdate) -> InventoryItem:
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item with id {item_id} not found."
        )
    for field, val in item_in.model_dump(exclude_unset=True).items():
        setattr(db_item, field, val)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_inventory_item(db: Session, item_id: int) -> None:
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item with id {item_id} not found."
        )
    db.delete(db_item)
    db.commit()
    return None


def batch_scan_inventory(db: Session, payload: InventoryBatchScanRequest) -> List[InventoryItem]:
    """
    Process scanned inventory items for a specific store:
    - If the item/class already exists in that store, accumulate on_hand (e.g. 3 + 3 = 6) and update freshness.
    - If new to that store, create a new inventory record with clean singular name and initial on_hand.
    - Atomic transaction in PostgreSQL; returns the full updated inventory list for that store.
    """
    target_store_id = payload.store_id if payload.store_id else 1
    store = db.query(Store).filter(Store.id == target_store_id).first()
    store_code = store.code if store else str(target_store_id)

    for item in payload.items:
        clean_label = item.class_label.strip().lower()
        if not clean_label or item.count <= 0:
            continue

        existing = db.query(InventoryItem).filter(
            InventoryItem.store_id == target_store_id,
            func.lower(InventoryItem.class_label) == clean_label
        ).first()

        meta = CLASS_METADATA.get(clean_label, {
            "singular": clean_label.replace("_", " ").title(),
            "plural": clean_label.replace("_", " ").title() + "s",
            "category": item.category or ("Produce" if "rotten" not in clean_label else "Spoilage Risk"),
            "isRotten": "_rotten" in clean_label,
            "baseFreshness": 15 if "_rotten" in clean_label else 95,
        })
        base_name = meta["singular"]
        if item.name and item.name.strip() and not any(char.isdigit() for char in item.name.split()[0]):
            base_name = item.name.strip()

        if existing:
            existing.on_hand += item.count
            if item.freshness is not None:
                existing.freshness_score = item.freshness
            if item.is_rotten or meta.get("isRotten", False):
                existing.is_spoilage_risk = True
                existing.status = "Spoiled / Flagged"
            else:
                existing.status = "In stock" if existing.on_hand > existing.min_stock else "Low stock"

            # If user provided a positive unit price, update it; otherwise preserve existing price
            if item.unit_price is not None and item.unit_price > 0:
                existing.unit_price = item.unit_price
        else:
            sku_code = f"SKU-{clean_label.upper().replace('_', '-')}-{store_code}"
            sku_exists = db.query(InventoryItem).filter(
                InventoryItem.store_id == target_store_id,
                InventoryItem.sku == sku_code
            ).first()
            if sku_exists:
                sku_code = f"{sku_code}-{secrets.randbelow(900) + 100}"

            price = item.unit_price if (item.unit_price is not None and item.unit_price >= 0) else 0.00
            freshness = item.freshness if item.freshness is not None else meta.get("baseFreshness", 95)
            is_rotten = bool(item.is_rotten or meta.get("isRotten", False))
            status_val = "Spoiled / Flagged" if is_rotten else ("In stock" if item.count > 20 else "Low stock")
            shelf = item.shelf_location or ("Write-off Bin" if is_rotten else "Aisle 1")

            new_item = InventoryItem(
                store_id=target_store_id,
                sku=sku_code,
                name=base_name,
                class_label=clean_label,
                category=item.category or meta.get("category", "Produce"),
                unit_price=price,
                on_hand=item.count,
                min_stock=20,
                freshness_score=freshness,
                is_spoilage_risk=is_rotten,
                status=status_val,
                shelf_location=shelf,
            )
            db.add(new_item)

    db.commit()
    return db.query(InventoryItem).filter(InventoryItem.store_id == target_store_id).order_by(InventoryItem.id).all()
