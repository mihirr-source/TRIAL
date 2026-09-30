"""Authentication tests for PARAKH Standards Recommendation Engine.

Covers:
- Password hashing & verification
- User registration (valid, duplicate, invalid input)
- User login (success, incorrect password, nonexistent user)
- Rate limiting / lockout on consecutive failed logins
- Session token creation, verification, and expiration
- /api/auth/me profile retrieval
- /api/auth/logout cookie clearing
- Route protection & redirection for unauthenticated access
"""

import os
import sqlite3
import tempfile
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bis_engine.auth import (
    COOKIE_NAME,
    create_signed_token,
    create_user,
    get_user_by_email,
    get_user_by_id,
    hash_password,
    init_db,
    verify_password,
    verify_signed_token,
    _failed_attempts,
)
from bis_engine.main import app


@pytest.fixture
def temp_db(monkeypatch):
    """Provide an isolated temporary SQLite database for auth testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = Path(tf.name)
    init_db(db_path)
    monkeypatch.setattr("bis_engine.auth.DEFAULT_DB_PATH", db_path)
    monkeypatch.setattr("bis_engine.auth.get_db_path", lambda: db_path)
    _failed_attempts.clear()
    yield db_path
    try:
        db_path.unlink(missing_ok=True)
    except Exception:
        pass


@pytest.fixture
def auth_client(temp_db):
    """TestClient bound to the app with temp database."""
    return TestClient(app)


def test_password_hashing():
    raw = "SuperSecurePassword123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_user_creation_and_retrieval(temp_db):
    user = create_user("officer@bis.gov.in", "Priya Sharma", "ValidPassword123!", db_path=temp_db)
    assert user["email"] == "officer@bis.gov.in"
    assert user["name"] == "Priya Sharma"
    assert "id" in user

    by_email = get_user_by_email("officer@bis.gov.in", db_path=temp_db)
    assert by_email is not None
    assert by_email["name"] == "Priya Sharma"

    by_id = get_user_by_id(user["id"], db_path=temp_db)
    assert by_id is not None
    assert by_id["email"] == "officer@bis.gov.in"


def test_signed_token_lifecycle():
    secret = "test-secret-key-12345"
    payload = {"sub": 42, "email": "test@example.com", "name": "Test User"}
    token = create_signed_token(payload, secret=secret, max_age=60)
    assert "." in token

    decoded = verify_signed_token(token, secret=secret)
    assert decoded is not None
    assert decoded["sub"] == 42
    assert decoded["email"] == "test@example.com"

    # Bad signature
    assert verify_signed_token(token, secret="wrong-secret") is None

    # Expired token
    expired_token = create_signed_token(payload, secret=secret, max_age=-10)
    assert verify_signed_token(expired_token, secret=secret) is None


def _register_and_verify(client: TestClient, email: str, name: str, password: str) -> dict:
    """Helper to perform complete registration flow (register + verify OTP)."""
    res = client.post(
        "/api/auth/register",
        json={"email": email, "name": name, "password": password},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "pending_verification"
    assert data["requires_otp"] is True
    
    # Verify OTP
    v_res = client.post(
        "/api/auth/verify-otp",
        json={"email": email, "token": data["otp_code_dev"], "reg_token": data["reg_token"]},
    )
    assert v_res.status_code == 200
    return v_res.json()


def test_register_endpoint_success(auth_client):
    res = auth_client.post(
        "/api/auth/register",
        json={"email": "tender.admin@nic.in", "name": "Admin User", "password": "SecurePassword123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "pending_verification"
    assert data["requires_otp"] is True
    assert data["email"] == "tender.admin@nic.in"
    assert "reg_token" in data
    assert data["cooldown_seconds"] == 60

    # Complete OTP verification
    v_res = auth_client.post(
        "/api/auth/verify-otp",
        json={"email": "tender.admin@nic.in", "token": data["otp_code_dev"], "reg_token": data["reg_token"]},
    )
    assert v_res.status_code == 200
    assert v_res.json()["status"] == "ok"
    assert v_res.json()["user"]["email"] == "tender.admin@nic.in"
    assert COOKIE_NAME in v_res.cookies


def test_register_duplicate_email_fails(auth_client):
    _register_and_verify(auth_client, "duplicate@nic.in", "User One", "SecurePassword123")
    
    res = auth_client.post(
        "/api/auth/register",
        json={"email": "duplicate@nic.in", "name": "User Two", "password": "SecurePassword123"},
    )
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


def test_register_validation_errors(auth_client):
    # Short password
    res = auth_client.post(
        "/api/auth/register",
        json={"email": "valid@test.com", "name": "Valid Name", "password": "short"},
    )
    assert res.status_code == 422

    # Invalid email
    res = auth_client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "name": "Valid Name", "password": "ValidPassword123"},
    )
    assert res.status_code == 422


def test_login_and_logout_flow(auth_client):
    # Register & verify first
    _register_and_verify(auth_client, "procurement@domain.org", "Procurement Officer", "Password123!")

    # Login
    res = auth_client.post(
        "/api/auth/login",
        json={"email": "procurement@domain.org", "password": "Password123!"},
    )
    assert res.status_code == 200
    assert COOKIE_NAME in res.cookies

    # Profile check with cookie
    me_res = auth_client.get("/api/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["user"]["email"] == "procurement@domain.org"

    # Logout
    logout_res = auth_client.post("/api/auth/logout")
    assert logout_res.status_code == 200


def test_login_invalid_password(auth_client):
    _register_and_verify(auth_client, "user@test.in", "Test User", "CorrectPassword123")

    res = auth_client.post(
        "/api/auth/login",
        json={"email": "user@test.in", "password": "WrongPassword123"},
    )
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_login_rate_limiting(auth_client):
    _failed_attempts.clear()
    for _ in range(5):
        auth_client.post(
            "/api/auth/login",
            json={"email": "locked@test.com", "password": "WrongPassword"},
        )

    # 6th attempt should trigger 429
    res = auth_client.post(
        "/api/auth/login",
        json={"email": "locked@test.com", "password": "WrongPassword"},
    )
    assert res.status_code == 429
    assert "Too many failed login attempts" in res.json()["detail"]


def test_protected_routes_with_auth_enforced(auth_client, monkeypatch):
    monkeypatch.setenv("BIS_ENFORCE_AUTH_TEST", "1")

    # Unauthenticated page request redirects (302) to /login
    res = auth_client.get("/", follow_redirects=False)
    assert res.status_code == 302
    assert res.headers["location"] == "/login"

    # Unauthenticated API request returns 401
    api_res = auth_client.get("/api/search?q=cement")
    assert api_res.status_code == 401
    assert "Authentication required" in api_res.json()["detail"]

    # Authenticate user and retry
    _register_and_verify(auth_client, "authuser@nic.in", "Auth User", "Password123!")

    auth_page_res = auth_client.get("/", follow_redirects=False)
    assert auth_page_res.status_code == 200

    auth_api_res = auth_client.get("/api/search?q=cement")
    assert auth_api_res.status_code == 200



def test_otp_verification_flow(auth_client):
    # 1. Register user -> initiates OTP flow
    res = auth_client.post(
        "/api/auth/register",
        json={"email": "new.vendor@gov.in", "name": "Vendor User", "password": "VendorSecret123!"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "pending_verification"
    assert data["requires_otp"] is True
    assert "reg_token" in data
    reg_token = data["reg_token"]
    otp_code = data.get("otp_code_dev")
    assert otp_code is not None

    # 2. Verify OTP with invalid token fails
    bad_verify = auth_client.post(
        "/api/auth/verify-otp",
        json={"email": "new.vendor@gov.in", "token": "000000", "reg_token": reg_token},
    )
    assert bad_verify.status_code == 400
    assert "Invalid or expired" in bad_verify.json()["detail"]

    # 3. Verify OTP with correct code succeeds and commits user to DB
    good_verify = auth_client.post(
        "/api/auth/verify-otp",
        json={"email": "new.vendor@gov.in", "token": otp_code, "reg_token": reg_token},
    )
    assert good_verify.status_code == 200
    assert good_verify.json()["status"] == "ok"
    assert COOKIE_NAME in good_verify.cookies

    # 4. Duplicate registration attempt for verified user should immediately fail with 400
    dup_res = auth_client.post(
        "/api/auth/register",
        json={"email": "new.vendor@gov.in", "name": "Vendor User", "password": "VendorSecret123!"},
    )
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 5. Logout and Login again with saved credentials
    auth_client.post("/api/auth/logout")
    login_res = auth_client.post(
        "/api/auth/login",
        json={"email": "new.vendor@gov.in", "password": "VendorSecret123!"},
    )
    assert login_res.status_code == 200
    assert login_res.json()["status"] == "ok"
    assert login_res.json()["user"]["email"] == "new.vendor@gov.in"


