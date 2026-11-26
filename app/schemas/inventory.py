from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

class InventoryBase(BaseModel):
    store_id: Optional[int] = 1
    sku: str
    name: str
    class_label: str
    category: str
    unit_price: Decimal
    on_hand: int
    min_stock: int
    freshness_score: int
    is_spoilage_risk: bool = False
    status: str = "In stock"
    shelf_location: str = "Aisle 1"

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    store_id: Optional[int] = None
    name: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[Decimal] = None
    on_hand: Optional[int] = None
    min_stock: Optional[int] = None
    freshness_score: Optional[int] = None
    is_spoilage_risk: Optional[bool] = None
    status: Optional[str] = None
    shelf_location: Optional[str] = None

class InventoryResponse(InventoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InventoryBatchScanItem(BaseModel):
    class_label: str
    name: Optional[str] = None
    category: Optional[str] = None
    count: int = 1
    freshness: Optional[int] = 100
    is_rotten: Optional[bool] = False
    unit_price: Optional[Decimal] = None
    shelf_location: Optional[str] = None

class InventoryBatchScanRequest(BaseModel):
    store_id: Optional[int] = 1
    items: list[InventoryBatchScanItem]
