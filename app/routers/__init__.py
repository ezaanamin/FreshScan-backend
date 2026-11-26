from fastapi import APIRouter
from .health import router as health_router
from .auth import router as auth_router
from .users import router as users_router
from .stores import router as stores_router
from .inventory import router as inventory_router
from .orders import router as orders_router
from .payment import router as payment_router
from .vision import router as vision_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(stores_router)
api_router.include_router(inventory_router)
api_router.include_router(orders_router)
api_router.include_router(payment_router)
api_router.include_router(vision_router)

__all__ = ["api_router"]
