from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class PaymentCardCreate(BaseModel):
    cardholder_name: str = Field(..., min_length=2, max_length=255)
    card_number: str = Field(..., min_length=12, max_length=24)
    expiry_date: str = Field(..., min_length=4, max_length=10) # e.g. "08/28" or "08 / 28"
    security_code: str = Field(..., min_length=3, max_length=4)
    billing_zip: str = Field(..., min_length=3, max_length=20)
    user_id: Optional[int] = None
    is_default: Optional[bool] = False

class PaymentMethodResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    cardholder_name: str
    card_number_masked: str
    card_last4: str
    card_brand: str
    expiry_month: str
    expiry_year: str
    billing_zip: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
