from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class StoreBase(BaseModel):
    code: str
    name: str
    address: str
    city: str
    store_type: str = "Supermarket"
    status: str = "Online / Active"
    camera_nodes: int = 4
    aisles: int = 12
    manager: str
    contact_phone: Optional[str] = None
    logo_url: Optional[str] = None
    currency: str = "USD"
    is_primary: bool = False

class StoreCreate(StoreBase):
    admin_name: Optional[str] = None
    admin_email: Optional[str] = None
    admin_password: Optional[str] = None

class StoreUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    store_type: Optional[str] = None
    status: Optional[str] = None
    camera_nodes: Optional[int] = None
    aisles: Optional[int] = None
    manager: Optional[str] = None
    contact_phone: Optional[str] = None
    logo_url: Optional[str] = None
    currency: Optional[str] = None
    is_primary: Optional[bool] = None

class StoreResponse(StoreBase):
    id: int
    created_at: datetime
    updated_at: datetime

    # Dynamic telemetry metrics computed on read
    on_hand_units: Optional[int] = 0
    inventory_valuation: Optional[Decimal] = Decimal("0.00")
    freshness_score: Optional[float] = 98.0
    spoilage_count: Optional[int] = 0

    # Assigned Store Admin Manager details
    admin_user_id: Optional[int] = None
    admin_email: Optional[str] = None
    admin_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
