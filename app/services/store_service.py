import os
import uuid
import shutil
from decimal import Decimal
from typing import List, Dict, Any
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from ..models.store import Store
from ..models.inventory import InventoryItem
from ..models.user import User
from ..schemas.store import StoreCreate, StoreUpdate, StoreResponse
from ..config import STATIC_DIR, UPLOAD_DIR


def get_stores(db: Session) -> List[StoreResponse]:
    stores = db.query(Store).order_by(Store.id).all()
    results = []
    for s in stores:
        items = db.query(InventoryItem).filter(InventoryItem.store_id == s.id).all()
        total_on_hand = sum(i.on_hand for i in items)
        total_val = sum((i.unit_price or 0) * i.on_hand for i in items)
        produce = [
            i for i in items
            if i.category and ('produce' in i.category.lower() or 'fruit' in i.category.lower() or 'veg' in i.category.lower())
        ]
        avg_fresh = (sum(p.freshness_score for p in produce) / len(produce)) if produce else 98.0
        spoil_count = sum(
            1 for i in items
            if i.status == "Spoiled / Flagged" or i.is_spoilage_risk or (i.freshness_score and i.freshness_score < 60)
        )

        resp = StoreResponse.model_validate(s)
        resp.on_hand_units = total_on_hand
        resp.inventory_valuation = total_val
        resp.freshness_score = round(avg_fresh, 1)
        resp.spoilage_count = spoil_count

        admin_user = db.query(User).filter(User.store_id == s.id, User.role == "STORE_ADMIN").first()
        if admin_user:
            resp.admin_user_id = admin_user.id
            resp.admin_email = admin_user.email
            resp.admin_name = admin_user.full_name

        results.append(resp)
    return results


def get_store(store_id: int, db: Session) -> StoreResponse:
    s = db.query(Store).filter(Store.id == store_id).first()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    items = db.query(InventoryItem).filter(InventoryItem.store_id == s.id).all()
    resp = StoreResponse.model_validate(s)
    resp.on_hand_units = sum(i.on_hand for i in items)
    resp.inventory_valuation = sum((i.unit_price or 0) * i.on_hand for i in items)
    produce = [
        i for i in items
        if i.category and ('produce' in i.category.lower() or 'fruit' in i.category.lower() or 'veg' in i.category.lower())
    ]
    resp.freshness_score = round((sum(p.freshness_score for p in produce) / len(produce)), 1) if produce else 98.0
    resp.spoilage_count = sum(
        1 for i in items
        if i.status == "Spoiled / Flagged" or i.is_spoilage_risk or (i.freshness_score and i.freshness_score < 60)
    )
    admin_user = db.query(User).filter(User.store_id == s.id, User.role == "STORE_ADMIN").first()
    if admin_user:
        resp.admin_user_id = admin_user.id
        resp.admin_email = admin_user.email
        resp.admin_name = admin_user.full_name
    return resp


def create_store(db: Session, store_in: StoreCreate) -> StoreResponse:
    clean_code = store_in.code.strip().replace("#", "")
    existing = db.query(Store).filter(Store.code == clean_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Store with code #{clean_code} already exists."
        )
    new_store = Store(
        code=clean_code,
        name=store_in.name.strip(),
        address=store_in.address.strip(),
        city=store_in.city.strip(),
        store_type=store_in.store_type,
        status=store_in.status,
        camera_nodes=store_in.camera_nodes,
        aisles=store_in.aisles,
        manager=store_in.manager.strip(),
        contact_phone=store_in.contact_phone,
        currency=store_in.currency or "USD",
        is_primary=store_in.is_primary,
    )
    db.add(new_store)
    db.flush()

    # Provision Store Admin Manager User Account
    admin_name = store_in.admin_name.strip() if (store_in.admin_name and store_in.admin_name.strip()) else store_in.manager.strip()
    admin_email = store_in.admin_email.strip().lower() if (store_in.admin_email and store_in.admin_email.strip()) else f"manager.{clean_code.lower()}@freshscan.io"
    admin_pwd = store_in.admin_password.strip() if (store_in.admin_password and store_in.admin_password.strip()) else f"Store{clean_code}!"

    existing_user = db.query(User).filter(User.email == admin_email).first()
    if existing_user:
        existing_user.store_id = new_store.id
        existing_user.role = "STORE_ADMIN"
        existing_user.full_name = admin_name
        admin_user_id = existing_user.id
    else:
        new_admin = User(
            full_name=admin_name,
            email=admin_email,
            password=admin_pwd,
            role="STORE_ADMIN",
            store_id=new_store.id,
        )
        db.add(new_admin)
        db.flush()
        admin_user_id = new_admin.id

    db.commit()
    db.refresh(new_store)
    resp = StoreResponse.model_validate(new_store)
    resp.on_hand_units = 0
    resp.inventory_valuation = Decimal("0.00")
    resp.freshness_score = 98.5
    resp.spoilage_count = 0
    resp.admin_user_id = admin_user_id
    resp.admin_email = admin_email
    resp.admin_name = admin_name
    return resp


def update_store(db: Session, store_id: int, store_in: StoreUpdate) -> StoreResponse:
    s = db.query(Store).filter(Store.id == store_id).first()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    data = store_in.model_dump(exclude_unset=True)
    # Store ID / Code is immutable once set and cannot be changed:
    data.pop("code", None)
    for field, val in data.items():
        setattr(s, field, val)
    db.commit()
    db.refresh(s)
    return get_store(store_id, db)


def delete_store(db: Session, store_id: int) -> None:
    s = db.query(Store).filter(Store.id == store_id).first()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    if s.is_primary or s.code == "104":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Primary flagship store cannot be deleted."
        )
    db.delete(s)
    db.commit()
    return None


def upload_store_logo(db: Session, store_id: int, file: UploadFile) -> Dict[str, Any]:
    s = db.query(Store).filter(Store.id == store_id).first()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    filename = file.filename or "logo.png"
    ext = os.path.splitext(filename)[1].lower()
    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format '{ext}'. Allowed formats: PNG, JPG, JPEG, WebP, SVG."
        )

    # Remove previous uploaded logo file if it exists in our upload directory
    if s.logo_url and s.logo_url.startswith("/static/uploads/logos/"):
        old_path = os.path.join(STATIC_DIR, s.logo_url.replace("/static/", "", 1))
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass

    unique_name = f"store_{store_id}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    logo_url = f"/static/uploads/logos/{unique_name}"
    s.logo_url = logo_url
    db.commit()
    db.refresh(s)

    return {
        "success": True,
        "logo_url": logo_url,
        "store": get_store(store_id, db),
    }


def remove_store_logo(db: Session, store_id: int) -> Dict[str, Any]:
    s = db.query(Store).filter(Store.id == store_id).first()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    if s.logo_url and s.logo_url.startswith("/static/uploads/logos/"):
        old_path = os.path.join(STATIC_DIR, s.logo_url.replace("/static/", "", 1))
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass

    s.logo_url = None
    db.commit()
    db.refresh(s)
    return {"success": True, "logo_url": None, "store": get_store(store_id, db)}
