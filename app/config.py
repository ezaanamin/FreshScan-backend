import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2:///freshscan_db")
APP_ENV = os.getenv("APP_ENV", "development")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

# Static & Upload Paths
STATIC_DIR = os.path.join(str(BASE_DIR), "static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads", "logos")
AVATAR_UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads", "avatars")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(AVATAR_UPLOAD_DIR, exist_ok=True)
