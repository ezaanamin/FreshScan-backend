from typing import List
from fastapi import APIRouter, Depends, status, File, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.user import UserCreate, UserResponse, UserUpdateRequest
from ..schemas.order import OrderResponse
from ..services.user_service import (
    create_user as svc_create_user,
    get_users as svc_get_users,
    get_user as svc_get_user,
    update_user as svc_update_user,
    upload_user_avatar as svc_upload_avatar,
)
from ..services.order_service import get_user_orders as svc_get_user_orders

router = APIRouter(tags=["Users"])


@router.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    return svc_create_user(db, user_in)


@router.get("/api/users", response_model=List[UserResponse])
def get_users(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return svc_get_users(db, skip=skip, limit=limit)


@router.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return svc_get_user(db, user_id)


@router.put("/api/users/{user_id}", response_model=UserResponse)
@router.put("/api/auth/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdateRequest, db: Session = Depends(get_db)):
    return svc_update_user(db, user_id, payload)


@router.post("/api/auth/users/{user_id}/avatar")
@router.post("/api/users/{user_id}/avatar")
async def upload_user_avatar(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    return svc_upload_avatar(db, user_id, file)


@router.get("/api/users/{user_id}/orders", response_model=List[OrderResponse])
def get_user_orders(user_id: int, db: Session = Depends(get_db)):
    return svc_get_user_orders(db, user_id)
