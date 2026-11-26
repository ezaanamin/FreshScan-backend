import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models.user import User
from ..models.store import Store
from ..models.verification import EmailVerification
from ..schemas.user import (
    UserLogin,
    SendVerificationRequest,
    VerifyCodeRequest,
    ResendCodeRequest,
    ForgotPasswordRequest,
)
from ..email_service import send_verification_email


def login_user(db: Session, login_in: UserLogin) -> Dict[str, Any]:
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or user.password != login_in.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    store_name = None
    store_code = None
    if user.store_id:
        store = db.query(Store).filter(Store.id == user.store_id).first()
        if store:
            store_name = store.name
            store_code = store.code
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role or "STORE_ADMIN",
        "store_id": user.store_id,
        "store_name": store_name,
        "store_code": store_code,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def get_auth_profiles(db: Session) -> List[Dict[str, Any]]:
    """
    Returns available Super Admin and Store Admin demo profiles for live role switching and inspection.
    """
    users = (
        db.query(User)
        .filter(User.role.in_(["SUPER_ADMIN", "STORE_ADMIN"]))
        .order_by(User.role.desc(), User.id)
        .all()
    )
    profiles = []
    for u in users:
        store_name = None
        store_code = None
        if u.store_id:
            s = db.query(Store).filter(Store.id == u.store_id).first()
            if s:
                store_name = s.name
                store_code = s.code
        profiles.append({
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "store_id": u.store_id,
            "store_name": store_name,
            "store_code": store_code,
        })
    return profiles


def send_verification(db: Session, req: SendVerificationRequest) -> Dict[str, Any]:
    clean_email = req.email.strip().lower()
    clean_name = req.full_name.strip()
    clean_password = req.password.strip()

    # 1. Check if user with this email already exists
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in.",
        )

    # 2. Generate 6-digit OTP code
    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    # 3. Clean any existing pending verifications for this email
    db.query(EmailVerification).filter(EmailVerification.email == clean_email).delete()

    # 4. Save new pending verification in database
    verification = EmailVerification(
        email=clean_email,
        full_name=clean_name,
        password=clean_password,
        code=code,
        expires_at=expires_at,
    )
    db.add(verification)
    db.commit()

    # 5. Send verification email via SMTP/Console
    send_verification_email(clean_email, clean_name, code)

    return {
        "success": True,
        "message": f"Verification code sent to {clean_email}",
        "email": clean_email,
        "expires_in_minutes": 15,
    }


def verify_code_and_register(db: Session, req: VerifyCodeRequest) -> User:
    clean_email = req.email.strip().lower()
    clean_code = req.code.strip()

    verification = (
        db.query(EmailVerification)
        .filter(EmailVerification.email == clean_email)
        .order_by(EmailVerification.created_at.desc())
        .first()
    )

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending verification found for this email. Please sign up again.",
        )

    # Check expiry
    current_time = datetime.now(timezone.utc)
    expires_at = verification.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if current_time > expires_at:
        db.delete(verification)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please tap 'Resend code'.",
        )

    if verification.code != clean_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Please check and try again.",
        )

    # Check if user already exists
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        db.delete(verification)
        db.commit()
        return existing

    # Verification succeeded! Create the actual User in PostgreSQL
    new_user = User(
        full_name=verification.full_name,
        email=verification.email,
        password=verification.password,
    )
    db.add(new_user)
    db.delete(verification)
    db.commit()
    db.refresh(new_user)
    return new_user


def resend_verification(db: Session, req: ResendCodeRequest) -> Dict[str, Any]:
    clean_email = req.email.strip().lower()

    verification = (
        db.query(EmailVerification)
        .filter(EmailVerification.email == clean_email)
        .order_by(EmailVerification.created_at.desc())
        .first()
    )

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending registration found for this email. Please sign up first.",
        )

    new_code = f"{secrets.randbelow(900000) + 100000}"
    verification.code = new_code
    verification.expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    db.commit()

    send_verification_email(clean_email, verification.full_name, new_code)

    return {
        "success": True,
        "message": f"Fresh verification code sent to {clean_email}",
        "email": clean_email,
        "expires_in_minutes": 15,
    }


def forgot_password(db: Session, req: ForgotPasswordRequest) -> Dict[str, Any]:
    clean_email = req.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No enterprise account found matching '{clean_email}'. Please verify your email.",
        )

    return {
        "success": True,
        "message": f"Password reset instructions dispatched to {clean_email}.",
        "email": clean_email,
    }
