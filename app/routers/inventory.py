from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.inventory import (
    InventoryCreate,
    InventoryResponse,
    InventoryUpdate,
    InventoryBatchScanRequest,
)
from ..services.inventory_service import (
    get_inventory as svc_get_inventory,
    get_inventory_item as svc_get_inventory_item,
    create_inventory_item as svc_create_inventory_item,
    update_inventory_item as svc_update_inventory_item,
    delete_inventory_item as svc_delete_inventory_item,
    batch_scan_inventory as svc_batch_scan_inventory,
)

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("", response_model=List[InventoryResponse])
@router.get("/", response_model=List[InventoryResponse])
def get_inventory(
    store_id: Optional[int] = None,
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
    spoilage_only: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return svc_get_inventory(
        db,
        store_id=store_id,
        category=category,
        status_filter=status_filter,
        spoilage_only=spoilage_only,
        search=search,
    )


@router.get("/{item_id}", response_model=InventoryResponse)
def get_inventory_item(item_id: int, db: Session = Depends(get_db)):
    return svc_get_inventory_item(db, item_id)


@router.post("", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
def create_inventory_item(item_in: InventoryCreate, db: Session = Depends(get_db)):
    return svc_create_inventory_item(db, item_in)


@router.put("/{item_id}", response_model=InventoryResponse)
def update_inventory_item(item_id: int, item_in: InventoryUpdate, db: Session = Depends(get_db)):
    return svc_update_inventory_item(db, item_id, item_in)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    return svc_delete_inventory_item(db, item_id)


@router.post("/batch-scan", response_model=List[InventoryResponse])
def batch_scan_inventory(payload: InventoryBatchScanRequest, db: Session = Depends(get_db)):
    return svc_batch_scan_inventory(db, payload)
