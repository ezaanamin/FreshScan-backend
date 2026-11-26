import sys
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.order import Order
from app.models.verification import EmailVerification

def run_tests():
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)

    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    assert res.json().get("database") == "connected"
    print("✓ Health check endpoint passed")

    # 2. User creation
    test_email = "alex.morgan@freshscan.io"
    db = SessionLocal()
    db.query(Order).filter(Order.receipt_code.in_(["FS-REC-98214", "FS-REC-INVALID"])).delete()
    db.query(User).filter(User.email == test_email).delete()
    db.commit()

    payload = {
        "full_name": "Alex Morgan",
        "email": test_email,
        "password": "Password123!",
    }
    res = client.post("/api/users", json=payload)
    assert res.status_code == 201, f"Create user failed: {res.text}"
    created_user = res.json()
    user_id = created_user["id"]
    print(f"✓ User created in PostgreSQL: id={user_id}")

    # 3. Duplicate email rejection
    res_dup = client.post("/api/users", json=payload)
    assert res_dup.status_code == 400
    print("✓ Duplicate email rejection verified")

    # 4. User login (success and failure)
    res_login_ok = client.post("/api/auth/login", json={"email": test_email, "password": "Password123!"})
    assert res_login_ok.status_code == 200
    assert res_login_ok.json()["id"] == user_id
    print("✓ User login with valid credentials verified")

    res_login_fail = client.post("/api/auth/login", json={"email": test_email, "password": "WrongPassword"})
    assert res_login_fail.status_code == 401
    print("✓ User login rejection on invalid password verified")

    # 5. Fetch user by id
    res_get = client.get(f"/api/users/{user_id}")
    assert res_get.status_code == 200
    assert res_get.json()["email"] == test_email
    print("✓ User retrieval verified")

    # 5. Create Order linked to User
    order_payload = {
        "user_id": user_id,
        "store_name": "Whole Foods – Downtown",
        "status": "completed",
        "subtotal": 17.14,
        "tax": 1.28,
        "total_amount": 18.42,
        "item_count": 4,
        "receipt_code": "FS-REC-98214",
    }
    res_order = client.post("/api/orders", json=order_payload)
    assert res_order.status_code == 201, f"Create order failed: {res_order.text}"
    created_order = res_order.json()
    assert created_order["user_id"] == user_id
    assert created_order["total_amount"] == 18.42
    assert created_order["receipt_code"] == "FS-REC-98214"
    print(f"✓ Order created linked to user: order_id={created_order['id']}, user_id={user_id}")

    # 6. Fetch user orders
    res_user_orders = client.get(f"/api/users/{user_id}/orders")
    assert res_user_orders.status_code == 200
    orders = res_user_orders.json()
    assert len(orders) == 1
    assert orders[0]["id"] == created_order["id"]
    print(f"✓ User orders query verified: {len(orders)} order(s) retrieved")

    # 7. Reject order for non-existent user
    res_invalid_order = client.post("/api/orders", json={**order_payload, "user_id": 999999, "receipt_code": "FS-REC-INVALID"})
    assert res_invalid_order.status_code == 404
    print("✓ Non-existent user order rejection verified")

    # 8. Clean up (cascade delete)
    db.query(Order).filter(Order.receipt_code.in_(["FS-REC-98214", "FS-REC-INVALID"])).delete()
    db.query(User).filter(User.email == test_email).delete()
    db.commit()

    # 9. Test Email Verification & Registration Flow (End-to-End)
    new_signup_email = "sarah.connor@freshscan.io"
    db.query(User).filter(User.email == new_signup_email).delete()
    db.query(EmailVerification).filter(EmailVerification.email == new_signup_email).delete()
    db.commit()

    # A. Send verification code
    signup_payload = {
        "full_name": "Sarah Connor",
        "email": new_signup_email,
        "password": "Terminator123!",
    }
    res_send = client.post("/api/auth/send-verification-code", json=signup_payload)
    assert res_send.status_code == 200, f"Send verification failed: {res_send.text}"
    assert res_send.json()["success"] is True
    print("✓ Send verification code endpoint passed and email triggered")

    # B. Retrieve generated code from database for verification
    verification_entry = db.query(EmailVerification).filter(EmailVerification.email == new_signup_email).first()
    assert verification_entry is not None
    otp_code = verification_entry.code
    assert len(otp_code) == 6
    print(f"✓ Verification code persisted in PostgreSQL: code={otp_code}")

    # C. Verify with wrong code (must fail)
    res_verify_fail = client.post("/api/auth/verify-code", json={"email": new_signup_email, "code": "000000"})
    assert res_verify_fail.status_code == 400
    print("✓ Invalid verification code rejected")

    # D. Resend code
    res_resend = client.post("/api/auth/resend-code", json={"email": new_signup_email})
    assert res_resend.status_code == 200
    db.refresh(verification_entry)
    new_otp_code = verification_entry.code
    print(f"✓ Resend code passed: new_code={new_otp_code}")

    # E. Verify with valid code (creates user in PostgreSQL)
    res_verify_ok = client.post("/api/auth/verify-code", json={"email": new_signup_email, "code": new_otp_code})
    assert res_verify_ok.status_code == 201, f"Verify code failed: {res_verify_ok.text}"
    new_user_data = res_verify_ok.json()
    assert new_user_data["email"] == new_signup_email
    assert new_user_data["full_name"] == "Sarah Connor"
    print(f"✓ Account activated & created in PostgreSQL via email verification: id={new_user_data['id']}")

    # F. Verify verification record is cleaned up
    assert db.query(EmailVerification).filter(EmailVerification.email == new_signup_email).first() is None
    print("✓ Pending verification record cleanly deleted after activation")

    # G. Log in with newly created account
    res_new_login = client.post("/api/auth/login", json={"email": new_signup_email, "password": "Terminator123!"})
    assert res_new_login.status_code == 200
    assert res_new_login.json()["id"] == new_user_data["id"]
    print("✓ Successfully logged in with newly verified account")

    # Final cleanup
    db.query(User).filter(User.email == new_signup_email).delete()
    db.commit()

    # 6. Inventory endpoints
    res_inv = client.get("/api/inventory")
    assert res_inv.status_code == 200
    assert len(res_inv.json()) >= 27
    print(f"✓ Inventory retrieval verified: {len(res_inv.json())} items loaded")

    res_inv_prod = client.get("/api/inventory?category=Produce")
    assert res_inv_prod.status_code == 200
    assert len(res_inv_prod.json()) > 0
    print(f"✓ Inventory category filter verified: {len(res_inv_prod.json())} Produce items")

    db.close()
    print("All backend tests, inventory endpoints, and email verification passed successfully!")

if __name__ == "__main__":
    run_tests()
