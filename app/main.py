from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import engine, Base
from .core.seeders import (
    seed_default_stores,
    seed_default_roles_and_users,
    seed_default_orders,
    seed_default_inventory,
    sync_db_sequences,
)
from .routers import api_router
from .config import STATIC_DIR
from fastapi import Request
from fastapi.responses import JSONResponse
import logging
import traceback

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically create tables in PostgreSQL on startup
    Base.metadata.create_all(bind=engine)
    seed_default_stores()
    seed_default_roles_and_users()
    seed_default_orders()
    seed_default_inventory()
    sync_db_sequences()
    yield


app = FastAPI(
    title="FreshScan API",
    description="Backend API for FreshScan grocery and freshness scanning platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for React Native mobile app and web clients
# Note: allow_credentials must be False when allow_origins is ["*"] per standard CORS spec
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches all unhandled exceptions, logs them with full traceback,
    and returns a structured JSON 500 error response with CORS headers
    so the browser does not reject it with a CORS Missing Header error.
    """
    tb = traceback.format_exc()
    logger.error(f"Unhandled Exception on {request.method} {request.url}: {exc}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {str(exc)}"},
        headers={"Access-Control-Allow-Origin": "*"},
    )

# Static directory for store logos & user uploads
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Mount modular API routers
app.include_router(api_router)
