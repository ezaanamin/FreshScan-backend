from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.user import (
    UserResponse,
    UserLogin,
    SendVerificationRequest,
    VerifyCodeRequest,
    ResendCodeRequest,
    VerificationResponse,
    ForgotPasswordRequest,
)
from ..services.auth_service import (
    login_user as auth_login,
    get_auth_profiles as auth_get_profiles,
    send_verification as auth_send_verification,
    verify_code_and_register as auth_verify_code,
    resend_verification as auth_resend_verification,
    forgot_password as auth_forgot_password,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=UserResponse)
def login_user(login_in: UserLogin, db: Session = Depends(get_db)):
    return auth_login(db, login_in)


@router.get("/profiles")
def get_auth_profiles(db: Session = Depends(get_db)):
    """
    Returns available Super Admin and Store Admin demo profiles for live role switching and inspection.
    """
    return auth_get_profiles(db)


@router.post("/send-verification-code", response_model=VerificationResponse)
def send_verification(req: SendVerificationRequest, db: Session = Depends(get_db)):
    return auth_send_verification(db, req)


@router.post("/verify-code", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def verify_code_and_register(req: VerifyCodeRequest, db: Session = Depends(get_db)):
    return auth_verify_code(db, req)


@router.post("/resend-code", response_model=VerificationResponse)
def resend_verification(req: ResendCodeRequest, db: Session = Depends(get_db)):
    return auth_resend_verification(db, req)


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return auth_forgot_password(db, req)
