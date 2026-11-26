import json
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models.order import Order
from ..models.user import User
from ..schemas.order import OrderCreate
from ..receipt_pdf import generate_receipt_pdf


def create_order(db: Session, order_in: OrderCreate) -> Order:
    user = db.query(User).filter(User.id == order_in.user_id).first()
    if not user:
        if order_in.user_id is None or order_in.user_id <= 0:
            fallback_user = db.query(User).order_by(User.id.asc()).first()
            if fallback_user:
                order_in.user_id = fallback_user.id
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {order_in.user_id} does not exist.",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {order_in.user_id} does not exist.",
            )

    new_order = Order(
        user_id=order_in.user_id,
        store_name=order_in.store_name,
        status=order_in.status,
        subtotal=order_in.subtotal,
        tax=order_in.tax,
        total_amount=order_in.total_amount,
        item_count=order_in.item_count,
        receipt_code=order_in.receipt_code,
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order


def get_orders(db: Session, skip: int = 0, limit: int = 50) -> List[Order]:
    return db.query(Order).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def get_user_orders(db: Session, user_id: int) -> List[Order]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return db.query(Order).order_by(Order.created_at.desc()).limit(50).all()
    return db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()


def generate_order_receipt_pdf(
    db: Session,
    receipt_code: str,
    store_name: Optional[str] = None,
    subtotal: Optional[float] = None,
    tax: Optional[float] = None,
    total: Optional[float] = None,
    currency_symbol: Optional[str] = "$",
    items_json: Optional[str] = None,
    created_at: Optional[str] = None,
) -> Tuple[bytes, str]:
    db_order = db.query(Order).filter(Order.receipt_code == receipt_code).first()

    final_store = store_name or (db_order.store_name if db_order else "FreshScan Partner Store")
    final_subtotal = subtotal if subtotal is not None else (db_order.subtotal if db_order else 0.0)
    final_tax = tax if tax is not None else (db_order.tax if db_order else 0.0)
    final_total = total if total is not None else (db_order.total_amount if db_order else 0.0)
    final_created_at = created_at or (
        db_order.created_at.strftime("%b %d, %Y · %I:%M %p") if db_order and db_order.created_at else None
    )

    items_list = []
    if items_json:
        try:
            items_list = json.loads(items_json)
        except Exception:
            items_list = []

    pdf_bytes = generate_receipt_pdf(
        receipt_code=receipt_code,
        store_name=final_store,
        items=items_list,
        subtotal=final_subtotal,
        tax=final_tax,
        total=final_total,
        currency_symbol=currency_symbol or "$",
        created_at=final_created_at,
    )

    clean_code = receipt_code.replace(" ", "_").replace("/", "_")
    filename = f"FreshScan_{clean_code}.pdf"
    return pdf_bytes, filename
