import re
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models.payment_method import PaymentMethod
from ..schemas.payment_method import PaymentCardCreate


def detect_card_brand(card_digits: str) -> str:
    cleaned = re.sub(r"\D", "", card_digits)
    if cleaned.startswith("4"):
        return "VISA"
    elif cleaned.startswith(("51", "52", "53", "54", "55")) or (cleaned[:4].isdigit() and 2221 <= int(cleaned[:4]) <= 2720):
        return "Mastercard"
    elif cleaned.startswith(("34", "37")):
        return "American Express"
    elif cleaned.startswith(("6011", "65")) or (cleaned[:3].isdigit() and 644 <= int(cleaned[:3]) <= 649):
        return "Discover"
    return "Card"


def add_payment_method(db: Session, card_in: PaymentCardCreate) -> PaymentMethod:
    """
    Saves a newly added credit/debit card to the PostgreSQL database.
    Securely stores masked card digits, expiration, cardholder name, and brand.
    """
    cleaned_digits = re.sub(r"\D", "", card_in.card_number)
    if len(cleaned_digits) < 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid card number format."
        )

    # Parse expiration
    parts = [p.strip() for p in card_in.expiry_date.split("/") if p.strip()]
    expiry_month = parts[0].zfill(2) if len(parts) > 0 else "01"
    expiry_year = parts[1] if len(parts) > 1 else "28"
    if len(expiry_year) == 2:
        expiry_year = f"20{expiry_year}"

    last4 = cleaned_digits[-4:]
    masked = f"•••• •••• •••• {last4}"
    brand = detect_card_brand(cleaned_digits)

    # Check if user already has cards
    existing_cards_query = db.query(PaymentMethod)
    if card_in.user_id:
        existing_cards_query = existing_cards_query.filter(PaymentMethod.user_id == card_in.user_id)
    existing_count = existing_cards_query.count()

    # First card is default, or if explicitly requested
    is_default = card_in.is_default or existing_count == 0

    if is_default:
        # Clear default flag on existing cards for this user
        if card_in.user_id:
            db.query(PaymentMethod).filter(PaymentMethod.user_id == card_in.user_id).update({"is_default": False})
        else:
            db.query(PaymentMethod).filter(PaymentMethod.user_id == None).update({"is_default": False})

    new_card = PaymentMethod(
        user_id=card_in.user_id,
        cardholder_name=card_in.cardholder_name.strip(),
        card_number_masked=masked,
        card_last4=last4,
        card_brand=brand,
        expiry_month=expiry_month,
        expiry_year=expiry_year,
        billing_zip=card_in.billing_zip.strip(),
        is_default=is_default,
    )

    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    return new_card


def get_payment_methods(db: Session, user_id: Optional[int] = None) -> List[PaymentMethod]:
    """
    Retrieves saved payment cards from the PostgreSQL database.
    """
    query = db.query(PaymentMethod)
    if user_id is not None:
        query = query.filter((PaymentMethod.user_id == user_id) | (PaymentMethod.user_id == None))
    return query.order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc()).all()


def delete_payment_method(db: Session, card_id: int) -> Dict[str, Any]:
    """
    Deletes a card payment method from PostgreSQL database by ID.
    """
    card = db.query(PaymentMethod).filter(PaymentMethod.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found."
        )

    was_default = card.is_default
    user_id = card.user_id
    db.delete(card)
    db.commit()

    # If the deleted card was default, set the next most recent card as default
    if was_default:
        next_card = db.query(PaymentMethod).filter(PaymentMethod.user_id == user_id).first()
        if next_card:
            next_card.is_default = True
            db.commit()

    return {"success": True, "message": "Payment method removed successfully."}


def set_default_payment_method(db: Session, card_id: int) -> PaymentMethod:
    """
    Sets a card as the default payment method in PostgreSQL.
    """
    card = db.query(PaymentMethod).filter(PaymentMethod.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found."
        )

    # Unset other defaults for this user
    if card.user_id:
        db.query(PaymentMethod).filter(PaymentMethod.user_id == card.user_id).update({"is_default": False})
    else:
        db.query(PaymentMethod).filter(PaymentMethod.user_id == None).update({"is_default": False})

    card.is_default = True
    db.commit()
    db.refresh(card)
    return card
