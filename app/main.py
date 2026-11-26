from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import engine, Base
from .core.seeders import seed_default_roles_and_users, seed_default_orders
from .routers import api_router
from .config import STATIC_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically create tables in PostgreSQL on startup
    Base.metadata.create_all(bind=engine)
    seed_default_roles_and_users()
    seed_default_orders()
    yield


app = FastAPI(
    title="FreshScan API",
    description="Backend API for FreshScan grocery and freshness scanning platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for React Native mobile app and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static directory for store logos & user uploads
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Mount modular API routers
app.include_router(api_router)
