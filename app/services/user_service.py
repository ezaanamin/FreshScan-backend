import os
import time
import shutil
from typing import List, Dict, Any
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from ..models.user import User
from ..models.store import Store
from ..schemas.user import UserCreate, UserUpdateRequest
from ..config import AVATAR_UPLOAD_DIR


def create_user(db: Session, user_in: UserCreate) -> User:
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    new_user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        password=user_in.password,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_users(db: Session, skip: int = 0, limit: int = 50) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


def get_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def update_user(db: Session, user_id: int, payload: UserUpdateRequest) -> Dict[str, Any]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if payload.full_name is not None and payload.full_name.strip():
        user.full_name = payload.full_name.strip()
    if payload.email is not None and payload.email.strip():
        user.email = payload.email.strip().lower()
    db.commit()
    db.refresh(user)
    store_name = None
    store_code = None
    if user.store_id:
        s = db.query(Store).filter(Store.id == user.store_id).first()
        if s:
            store_name = s.name
            store_code = s.code
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


def upload_user_avatar(db: Session, user_id: int, file: UploadFile) -> Dict[str, Any]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    file_ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    safe_filename = f"user_{user_id}_{int(time.time())}{file_ext}"
    dest_path = os.path.join(AVATAR_UPLOAD_DIR, safe_filename)

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    avatar_url = f"/static/uploads/avatars/{safe_filename}"
    return {"success": True, "avatar_url": avatar_url}
