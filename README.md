# FreshScan Backend API

The high-performance REST API backend powering **FreshScan** (React Native mobile app) and the **FreshScan Retail Operations Dashboard** (React web dashboard). 

Built with **FastAPI**, **PostgreSQL** (SQLAlchemy ORM), **YOLO11** computer vision inference, **ReportLab** PDF generation, and designed using a **modular layered architecture** (Routers, Services/Controllers, and Core/Seeders).

---

## Table of Contents
1. [Tech Stack](#tech-stack)
2. [Modular Architecture](#modular-architecture)
3. [Features](#features)
4. [Environment Variables](#environment-variables)
5. [Local Development Setup](#local-development-setup)
6. [Docker Deployment](#docker-deployment)
7. [AWS EC2 Deployment Guide](#aws-ec2-deployment-guide)
8. [API Endpoints Reference](#api-endpoints-reference)
9. [Pre-Seeded Accounts](#pre-seeded-accounts)
10. [Running Tests](#running-tests)

---

## Tech Stack

* **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
* **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)
* **Database**: [PostgreSQL](https://www.postgresql.org/) 16
* **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) + [Psycopg2](https://www.psycopg.org/)
* **Validation**: [Pydantic v2](https://docs.pydantic.dev/)
* **AI & Computer Vision**: [Ultralytics YOLO11](https://docs.ultralytics.com/) (`best_model/best.pt`) + Pillow
* **Receipt Generation**: [ReportLab](https://www.reportlab.com/) (Vector PDF invoices)
* **Email Verification**: Google Gmail API / OAuth2

---

## Modular Architecture

The backend follows an enterprise-grade layered architecture separating HTTP routing, business logic/controllers, database models, and application lifecycle:

```
backend/
├── app/
│   ├── core/                     # Initialization, Config & Lifecycle Seeders
│   │   ├── __init__.py           # Core exports
│   │   ├── config.py             # Environment configuration & static directories
│   │   ├── database.py           # SQLAlchemy database engine & SessionLocal factory
│   │   └── seeders.py            # Startup seeders (roles, users, trip history)
│   ├── services/                 # Business Logic & Controller Layer
│   │   ├── __init__.py           # Service exports
│   │   ├── auth_service.py       # Authentication, demo profiles, OTP & password reset
│   │   ├── user_service.py       # Profile updates, user queries, avatar uploads
│   │   ├── store_service.py      # Store CRUD, logo uploads, manager provisioning
│   │   ├── inventory_service.py  # Inventory filtering, CRUD, atomic batch scans
│   │   ├── order_service.py      # Order creation, trip history, PDF receipts
│   │   └── payment_service.py    # Masked card tokens, brand detection, defaults
│   ├── routers/                  # HTTP API Routers (FastAPI APIRouter)
│   │   ├── __init__.py           # Central api_router aggregator
│   │   ├── health.py             # / and /health
│   │   ├── auth.py               # /api/auth/*
│   │   ├── users.py              # /api/users/*
│   │   ├── stores.py             # /api/stores/*
│   │   ├── inventory.py          # /api/inventory/*
│   │   ├── orders.py             # /api/orders/*
│   │   ├── payment.py            # /api/payment-methods/*
│   │   └── vision.py             # /api/vision/*
│   ├── models/                   # SQLAlchemy ORM Models
│   │   ├── inventory.py          # Inventory & SKU tracking
│   │   ├── order.py              # Checkout orders & trip history
│   │   ├── payment_method.py     # Saved payment cards & tokens
│   │   ├── store.py              # Multi-store locations & settings
│   │   ├── user.py               # User profiles & role-based authentication
│   │   └── verification.py       # Email OTP codes & expiration
│   ├── schemas/                  # Pydantic Request/Response Schemas
│   │   ├── inventory.py
│   │   ├── order.py
│   │   ├── payment_method.py
│   │   ├── store.py
│   │   └── user.py
│   ├── email_service.py          # Gmail API integration for verification codes
│   ├── receipt_pdf.py            # PDF invoice generation via ReportLab
│   ├── vision_service.py         # YOLO11 inference, classes metadata, freshness assessment
│   └── main.py                   # Lightweight entrypoint (< 50 lines)
├── static/                       # Static file storage (served at /static)
│   └── uploads/
│       ├── avatars/              # Shopper profile avatars
│       └── logos/                # Retail store brand logos
├── requirements.txt              # Python package dependencies
├── Dockerfile                    # Production container specification
├── .dockerignore                 # Docker build exclusion rules
├── .env.example                  # Environment variables template
└── test_api.py                   # Integration test suite
```

---

## Features

* **Layered Architecture**: Full separation between HTTP handling (Routers) and business logic (Services/Controllers) with a lightweight, clean entrypoint.
* **Multi-Store Retail Network**: Supports multi-tenant grocery chains with store-specific pricing, currency, inventory, aisles, managers, and brand logos.
* **Computer Vision Scanning**: YOLO11 model inference supporting 27 retail produce classes with bounding boxes, item counts, and automated produce freshness/spoilage scoring.
* **Role-Based Authentication**: Seamless switching between `SUPER_ADMIN`, `STORE_ADMIN`, and `CUSTOMER` roles.
* **Trip History & Digital Receipts**: Automated order checkout with tax calculation, Fresh Rewards points, and vector PDF receipt generation (`/api/orders/{receipt_code}/pdf`).
* **Automated Startup Seeders**: Automatically provisions default store admins, flagship stores, produce inventory, and sample orders on clean database boots.

---

## Environment Variables

Create a `.env` file in the `backend/` directory based on `.env.example`:

```env
# Database connection string
DATABASE_URL=postgresql+psycopg2://freshscan_user:freshscan_password@localhost:5432/freshscan_db

# Environment & Port
APP_ENV=development
APP_PORT=8000

# Optional: Path to YOLO11 model weights (defaults to ../best_model/best.pt)
MODEL_PATH=/path/to/best_model/best.pt
```

---

## Local Development Setup

### 1. Prerequisites
* Python 3.12+
* PostgreSQL 14+ running locally (or via Docker)

### 2. Create Virtual Environment & Install Dependencies
```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate       # On Linux/macOS
# .\venv\Scripts\activate      # On Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Start FastAPI Server
```bash
# Start FastAPI with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

* **API Root**: [http://localhost:8000/](http://localhost:8000/)
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
* **Interactive Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Alternative Docs (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Docker Deployment

The backend is fully containerized and includes a multi-stage Docker build with built-in healthchecks.

### Standalone Docker Build
```bash
cd backend

# Build Docker image
docker build -t freshscan-backend .

# Run container (connecting to external database)
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+psycopg2://user:password@host:5432/freshscan_db" \
  --name freshscan_backend \
  freshscan-backend
```

### Full Stack Orchestration (via Docker Compose)
From the repository root:
```bash
# Starts PostgreSQL (5433), Backend (8000), and Web Dashboard (8080)
docker compose up -d --build
```

Check container health:
```bash
docker compose ps
```

---

## AWS EC2 Deployment Guide

1. **Connect to your EC2 instance**:
   ```bash
   ssh -i "your-key.pem" ubuntu@<YOUR_AWS_PUBLIC_IP>
   ```

2. **Install Docker & Docker Compose**:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
   sudo usermod -aG docker $USER && newgrp docker
   ```

3. **Deploy the Stack**:
   ```bash
   git clone <YOUR_REPO_URL> freshscan
   cd freshscan
   cp .env.docker.example .env
   docker compose up -d --build
   ```

4. **Verify Deployment**:
   ```bash
   curl http://localhost:8000/health
   # {"status":"healthy","database":"connected","db_check":1}
   ```
   Access Swagger UI at `http://<YOUR_AWS_PUBLIC_IP>:8000/docs` and the Web Dashboard at `http://<YOUR_AWS_PUBLIC_IP>:8080`.

---

## API Endpoints Reference

### Health & System
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API service status & version info |
| `GET` | `/health` | Database connection health check |

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Authenticate user with email and password |
| `GET` | `/api/auth/profiles` | List demo admin & store manager accounts |
| `POST` | `/api/auth/send-verification-code` | Send 6-digit OTP code to email |
| `POST` | `/api/auth/verify-code` | Validate OTP code and activate account |
| `POST` | `/api/auth/resend-code` | Resend fresh 6-digit verification code |
| `POST` | `/api/auth/forgot-password` | Dispatch password reset instructions |

### Users
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/users` | Register new customer account |
| `GET` | `/api/users` | List users (paginated) |
| `GET` | `/api/users/{id}` | Get user profile by ID |
| `PUT` | `/api/users/{id}` | Update user name and email |
| `POST` | `/api/auth/users/{id}/avatar` | Upload profile avatar image |
| `GET` | `/api/users/{id}/orders` | Get user order history |

### Stores Management
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/stores` | List all stores with inventory valuation and freshness metrics |
| `POST` | `/api/stores` | Provision new store & assign store admin manager |
| `GET` | `/api/stores/{id}` | Get specific store details |
| `PUT` | `/api/stores/{id}` | Update store details |
| `DELETE` | `/api/stores/{id}` | Delete store (primary flagship store protected) |
| `POST` | `/api/stores/{id}/upload-logo` | Upload custom store brand logo |
| `DELETE` | `/api/stores/{id}/logo` | Remove custom store logo |

### Inventory & Spoilage
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/inventory` | Query inventory (filters: `store_id`, `category`, `status`, `search`) |
| `GET` | `/api/inventory/{id}` | Get specific inventory item |
| `POST` | `/api/inventory` | Create manual inventory item |
| `PUT` | `/api/inventory/{id}` | Update item price, quantity, or location |
| `DELETE` | `/api/inventory/{id}` | Remove inventory item |
| `POST` | `/api/inventory/batch-scan` | Batch insert/accumulate scanned produce items |

### Orders & Receipts
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/orders` | List checkout orders (paginated, newest first) |
| `POST` | `/api/orders` | Create completed order & record trip history |
| `GET` | `/api/orders/{receipt_code}/pdf` | Download vector PDF receipt with itemized breakdown |

### Payment Methods
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/payment-methods` | List saved payment cards (masked) |
| `POST` | `/api/payment-methods` | Add new payment card (auto-detects brand) |
| `DELETE` | `/api/payment-methods/{id}` | Remove payment card |
| `PATCH` | `/api/payment-methods/{id}/default` | Set card as primary payment method |

### Computer Vision (YOLO11)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/vision/classes` | Get supported 27 produce classes & baseline freshness |
| `POST` | `/api/vision/detect` | Run YOLO11 object detection on multipart image file |
| `POST` | `/api/vision/detect-base64` | Run YOLO11 inference on base64 snapshot (webcam/app) |

---

## Pre-Seeded Accounts

When the database is initialized, default admin accounts are seeded automatically:

| Email | Password | Role | Assigned Store |
|---|---|---|---|
| `admin@freshscan.io` | `Admin123!` | `SUPER_ADMIN` | All Stores (Flagship) |
| `alex.morgan@freshscan.io` | `Store104!` | `STORE_ADMIN` | Store #104 (Downtown Supermarket) |
| `elena.vance@freshscan.io` | `Store108!` | `STORE_ADMIN` | Store #108 |
| `marcus.reed@freshscan.io` | `Store112!` | `STORE_ADMIN` | Store #112 |
| `sarah.chen@freshscan.io` | `Store120!` | `STORE_ADMIN` | Store #120 |

---

## Running Tests

Run the backend integration test suite to verify all endpoints, database queries, and email verification:

```bash
cd backend
source venv/bin/activate
python test_api.py
```
