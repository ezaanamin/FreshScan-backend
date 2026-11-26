from typing import List, Optional
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.order import OrderCreate, OrderResponse
from ..services.order_service import (
    create_order as svc_create_order,
    get_orders as svc_get_orders,
    generate_order_receipt_pdf as svc_generate_order_pdf,
)

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_in: OrderCreate, db: Session = Depends(get_db)):
    return svc_create_order(db, order_in)


@router.get("", response_model=List[OrderResponse])
@router.get("/", response_model=List[OrderResponse])
def get_orders(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return svc_get_orders(db, skip=skip, limit=limit)


@router.get("/{receipt_code}/pdf")
def get_order_receipt_pdf(
    receipt_code: str,
    store_name: Optional[str] = None,
    subtotal: Optional[float] = None,
    tax: Optional[float] = None,
    total: Optional[float] = None,
    currency_symbol: Optional[str] = "$",
    items_json: Optional[str] = None,
    created_at: Optional[str] = None,
    db: Session = Depends(get_db),
):
    pdf_bytes, filename = svc_generate_order_pdf(
        db,
        receipt_code=receipt_code,
        store_name=store_name,
        subtotal=subtotal,
        tax=tax,
        total=total,
        currency_symbol=currency_symbol,
        items_json=items_json,
        created_at=created_at,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/pdf",
        },
    )
