from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.payment_method import PaymentCardCreate, PaymentMethodResponse
from ..services.payment_service import (
    add_payment_method as svc_add_payment_method,
    get_payment_methods as svc_get_payment_methods,
    delete_payment_method as svc_delete_payment_method,
    set_default_payment_method as svc_set_default,
)

router = APIRouter(prefix="/api/payment-methods", tags=["Payment Methods"])


@router.post("", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
def add_payment_method(card_in: PaymentCardCreate, db: Session = Depends(get_db)):
    return svc_add_payment_method(db, card_in)


@router.get("", response_model=List[PaymentMethodResponse])
@router.get("/", response_model=List[PaymentMethodResponse])
def get_payment_methods(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    return svc_get_payment_methods(db, user_id=user_id)


@router.delete("/{card_id}", status_code=status.HTTP_200_OK)
def delete_payment_method(card_id: int, db: Session = Depends(get_db)):
    return svc_delete_payment_method(db, card_id)


@router.patch("/{card_id}/default", response_model=PaymentMethodResponse)
def set_default_payment_method(card_id: int, db: Session = Depends(get_db)):
    return svc_set_default(db, card_id)
