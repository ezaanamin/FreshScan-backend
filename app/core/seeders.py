from datetime import datetime, timedelta
from ..database import SessionLocal
from ..models.user import User
from ..models.order import Order
from ..models.store import Store


def seed_default_roles_and_users():
    """
    Ensures core roles and user accounts with passwords exist in PostgreSQL:
    - Super Admin: admin@freshscan.io (role: SUPER_ADMIN)
    - Store Admins: alex.morgan, elena.vance, marcus.reed, sarah.chen (role: STORE_ADMIN)
    """
    db = SessionLocal()
    try:
        super_admin = db.query(User).filter(User.email == "admin@freshscan.io").first()
        if not super_admin:
            db.add(User(
                full_name="Super Admin",
                email="admin@freshscan.io",
                password="Admin123!",
                role="SUPER_ADMIN",
                store_id=None
            ))
        else:
            super_admin.role = "SUPER_ADMIN"
            if not super_admin.password:
                super_admin.password = "Admin123!"

        store_admins = [
            ("Alex Morgan", "alex.morgan@freshscan.io", "Store104!", "104"),
            ("Elena Vance", "elena.vance@freshscan.io", "Store108!", "108"),
            ("Marcus Reed", "marcus.reed@freshscan.io", "Store112!", "112"),
            ("Sarah Chen", "sarah.chen@freshscan.io", "Store120!", "120"),
        ]
        for name, email, pwd, code in store_admins:
            st = db.query(Store).filter(Store.code == code).first()
            store_id = st.id if st else None
            u = db.query(User).filter(User.email == email).first()
            if not u:
                db.add(User(
                    full_name=name,
                    email=email,
                    password=pwd,
                    role="STORE_ADMIN",
                    store_id=store_id
                ))
            else:
                u.role = "STORE_ADMIN"
                u.password = pwd
                if store_id:
                    u.store_id = store_id

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding roles and users: {e}")
    finally:
        db.close()


def seed_default_orders():
    """
    Ensures default realistic trip history exists in PostgreSQL.
    """
    db = SessionLocal()
    try:
        existing_count = db.query(Order).count()
        if existing_count == 0:
            users = db.query(User).all()
            if not users:
                return

            now = datetime.now()
            sample_orders = [
                {
                    "store_name": "Downtown Supermarket",
                    "status": "completed",
                    "subtotal": 12.80,
                    "tax": 1.02,
                    "total_amount": 13.82,
                    "item_count": 5,
                    "receipt_code": "FS-REC-89241",
                    "created_at": now - timedelta(hours=2),
                },
                {
                    "store_name": "Downtown Supermarket",
                    "status": "completed",
                    "subtotal": 7.40,
                    "tax": 0.59,
                    "total_amount": 7.99,
                    "item_count": 3,
                    "receipt_code": "FS-REC-76190",
                    "created_at": now - timedelta(days=1, hours=4),
                },
                {
                    "store_name": "Organic Valley Hub",
                    "status": "completed",
                    "subtotal": 21.50,
                    "tax": 1.72,
                    "total_amount": 23.22,
                    "item_count": 8,
                    "receipt_code": "FS-REC-65412",
                    "created_at": now - timedelta(days=3),
                },
                {
                    "store_name": "Metro Green Grocers",
                    "status": "completed",
                    "subtotal": 9.20,
                    "tax": 0.74,
                    "total_amount": 9.94,
                    "item_count": 4,
                    "receipt_code": "FS-REC-54098",
                    "created_at": now - timedelta(days=6),
                },
            ]
            for u in users:
                for idx, o in enumerate(sample_orders):
                    new_ord = Order(
                        user_id=u.id,
                        store_name=o["store_name"],
                        status=o["status"],
                        subtotal=o["subtotal"],
                        tax=o["tax"],
                        total_amount=o["total_amount"],
                        item_count=o["item_count"],
                        receipt_code=f"{o['receipt_code']}-{u.id}",
                        created_at=o["created_at"],
                    )
                    db.add(new_ord)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding default orders: {e}")
    finally:
        db.close()
