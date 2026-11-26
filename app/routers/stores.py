from typing import List
from fastapi import APIRouter, Depends, status, File, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.store import StoreCreate, StoreUpdate, StoreResponse
from ..services.store_service import (
    get_stores as svc_get_stores,
    get_store as svc_get_store,
    create_store as svc_create_store,
    update_store as svc_update_store,
    delete_store as svc_delete_store,
    upload_store_logo as svc_upload_logo,
    remove_store_logo as svc_remove_logo,
)

router = APIRouter(prefix="/api/stores", tags=["Stores"])


@router.get("", response_model=List[StoreResponse])
@router.get("/", response_model=List[StoreResponse])
def get_stores(db: Session = Depends(get_db)):
    return svc_get_stores(db)


@router.get("/{store_id}", response_model=StoreResponse)
def get_store(store_id: int, db: Session = Depends(get_db)):
    return svc_get_store(store_id, db)


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
def create_store(store_in: StoreCreate, db: Session = Depends(get_db)):
    return svc_create_store(db, store_in)


@router.put("/{store_id}", response_model=StoreResponse)
def update_store(store_id: int, store_in: StoreUpdate, db: Session = Depends(get_db)):
    return svc_update_store(db, store_id, store_in)


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_store(store_id: int, db: Session = Depends(get_db)):
    return svc_delete_store(db, store_id)


@router.post("/{store_id}/upload-logo")
async def upload_store_logo(store_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    return svc_upload_logo(db, store_id, file)


@router.delete("/{store_id}/logo")
def remove_store_logo(store_id: int, db: Session = Depends(get_db)):
    return svc_remove_logo(db, store_id)
