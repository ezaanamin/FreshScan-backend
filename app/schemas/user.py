from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    role: str = "STORE_ADMIN"
    store_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    store_name: Optional[str] = None
    store_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SendVerificationRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str

class ResendCodeRequest(BaseModel):
    email: EmailStr

class VerificationResponse(BaseModel):
    success: bool
    message: str
    email: EmailStr
    expires_in_minutes: int = 15

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
