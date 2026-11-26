from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db

router = APIRouter(tags=["Health & Status"])


@router.get("/")
def read_root():
    return {
        "app": "FreshScan API",
        "version": "1.0.0",
        "status": "online",
    }


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).scalar()
        return {
            "status": "healthy",
            "database": "connected",
            "db_check": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}",
        )
