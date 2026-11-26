from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class OrderBase(BaseModel):
    store_name: str = "Whole Foods – Downtown"
    status: str = "completed"
    subtotal: float = 0.00
    tax: float = 0.00
    total_amount: float = 0.00
    item_count: int = 0
    receipt_code: Optional[str] = None

class OrderCreate(OrderBase):
    user_id: int

class OrderResponse(OrderBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
