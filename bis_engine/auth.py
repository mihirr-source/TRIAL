"""Authentication and user management for PARAKH Standards Recommendation Engine.

Provides:
- SQLite persistence (bis_engine/data/users.db)
- Bcrypt password hashing
- Signed session cookie tokens
- Input validation (email regex, password length >= 8)
- Failed login rate-limiting / temporary lockout
- FastAPI dependencies & auth endpoints (/api/auth/*)
"""

from __future__ import annotations

import hmac
import hashlib
import json
import os
import re
import sqlite3
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from pathlib import Path
from typing import Any, Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator

# --------------------------------------------------------------------- config & paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "users.db"

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR.parent / ".env")
    load_dotenv()
except ImportError:
    pass

SECRET_KEY = os.environ.get("SECRET_KEY", "bis-standards-default-secret-key-change-in-prod-2026")
COOKIE_NAME = "bis_session"
SESSION_DURATION = 7 * 24 * 3600  # 7 days in seconds

# Rate limiting: max 5 failed attempts per IP/email within 300s -> lockout for 300s
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW = 300  # 5 minutes
_failed_attempts: dict[str, list[float]] = {}

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


# --------------------------------------------------------------------- database
def get_db_path() -> Path:
    custom = os.environ.get("BIS_DB_PATH")
    if custom:
        p = Path(custom)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    # On Vercel / AWS Lambda / Serverless read-only filesystems, use /tmp
    is_serverless = bool(
        os.environ.get("VERCEL")
        or os.environ.get("VERCEL_ENV")
        or os.environ.get("NOW_REGION")
        or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
        or os.environ.get("LAMBDA_TASK_ROOT")
        or os.environ.get("K_SERVICE")
    )
    if is_serverless:
        tmp_dir = Path("/tmp")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir / "users.db"

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        test_path = DATA_DIR / ".write_test"
        with open(test_path, "w") as f:
            f.write("ok")
        test_path.unlink(missing_ok=True)
        return DEFAULT_DB_PATH
    except (OSError, PermissionError):
        tmp_dir = Path("/tmp")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir / "users.db"


def get_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    try:
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        return conn
    except (sqlite3.OperationalError, PermissionError, OSError):
        # Fallback to /tmp if current path was read-only
        tmp_path = Path("/tmp") / "users.db"
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(tmp_path))
        conn.row_factory = sqlite3.Row
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        return conn


def init_db(db_path: Optional[Path] = None) -> None:
    try:
        conn = get_db(db_path)
        conn.close()
    except Exception:
        pass


# Ensure DB tables exist on import
init_db()


# --------------------------------------------------------------------- password & tokens
def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_signed_token(payload: dict[str, Any], secret: str = SECRET_KEY, max_age: int = SESSION_DURATION) -> str:
    """Create a URL-safe HMAC-SHA256 signed JSON token with expiration."""
    exp = int(time.time()) + max_age
    token_data = {**payload, "exp": exp}
    raw_bytes = json.dumps(token_data, separators=(",", ":")).encode("utf-8")
    b64_payload = urlsafe_b64encode(raw_bytes).decode("utf-8").rstrip("=")
    
    sig = hmac.new(secret.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).digest()
    b64_sig = urlsafe_b64encode(sig).decode("utf-8").rstrip("=")
    
    return f"{b64_payload}.{b64_sig}"


def verify_signed_token(token: str, secret: str = SECRET_KEY) -> Optional[dict[str, Any]]:
    """Verify signed token signature and expiration timestamp."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        b64_payload, b64_sig = parts
        
        # Verify HMAC signature
        expected_sig = hmac.new(secret.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).digest()
        expected_b64_sig = urlsafe_b64encode(expected_sig).decode("utf-8").rstrip("=")
        if not hmac.compare_digest(b64_sig, expected_b64_sig):
            return None
        
        # Decode payload
        padding = "=" * (4 - len(b64_payload) % 4) if len(b64_payload) % 4 != 0 else ""
        raw_json = urlsafe_b64decode(b64_payload + padding).decode("utf-8")
        data = json.loads(raw_json)
        
        # Check expiration
        if data.get("exp", 0) < time.time():
            return None
            
        return data
    except Exception:
        return None


# --------------------------------------------------------------------- rate limiting
def _check_rate_limit(key: str) -> None:
    now = time.time()
    attempts = [t for t in _failed_attempts.get(key, []) if now - t < LOCKOUT_WINDOW]
    _failed_attempts[key] = attempts
    if len(attempts) >= MAX_FAILED_ATTEMPTS:
        remaining = int(LOCKOUT_WINDOW - (now - attempts[0]))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Please try again in {max(1, remaining)} seconds.",
        )


def _record_failed_attempt(key: str) -> None:
    now = time.time()
    attempts = [t for t in _failed_attempts.get(key, []) if now - t < LOCKOUT_WINDOW]
    attempts.append(now)
    _failed_attempts[key] = attempts


def _clear_failed_attempts(key: str) -> None:
    _failed_attempts.pop(key, None)


# --------------------------------------------------------------------- user queries
def get_user_by_email(email: str, db_path: Optional[Path] = None) -> Optional[sqlite3.Row]:
    conn = get_db(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
        return cur.fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id: int, db_path: Optional[Path] = None) -> Optional[sqlite3.Row]:
    conn = get_db(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cur.fetchone()
    finally:
        conn.close()


def create_user(email: str, name: str, password: str, db_path: Optional[Path] = None) -> dict[str, Any]:
    email = email.strip().lower()
    name = name.strip()
    pwd_hash = hash_password(password)
    
    conn = get_db(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)",
                (email, name, pwd_hash),
            )
            user_id = cur.lastrowid
            return {"id": user_id, "email": email, "name": name}
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )
    finally:
        conn.close()


# --------------------------------------------------------------------- schemas
class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars)")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_REGEX.match(v):
            raise ValueError("Please provide a valid email address.")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class LoginRequest(BaseModel):
    email: str = Field(...)
    password: str = Field(...)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("Email is required.")
        return v


# --------------------------------------------------------------------- auth router
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_current_user_optional(request: Request) -> Optional[dict[str, Any]]:
    """Retrieve authenticated user from signed session cookie, or None."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        # Check Authorization header as fallback: Bearer <token>
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            
    if not token:
        return None
        
    payload = verify_signed_token(token)
    if not payload or "sub" not in payload:
        return None
        
    user = get_user_by_id(payload["sub"])
    if not user:
        return None
        
    return {"id": user["id"], "email": user["email"], "name": user["name"]}


def get_current_user(request: Request) -> dict[str, Any]:
    """Dependency: require authenticated user, raising 401 otherwise."""
    user = get_current_user_optional(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
        )
    return user


def set_auth_cookie(response: Response, user: dict[str, Any]) -> None:
    token = create_signed_token({"sub": user["id"], "email": user["email"], "name": user["name"]})
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_DURATION,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True when SSL/TLS is active
        path="/",
    )


@auth_router.post("/register")
def register(req: RegisterRequest, response: Response) -> dict[str, Any]:
    try:
        user = create_user(email=req.email, name=req.name, password=req.password)
        set_auth_cookie(response, user)
        return {"status": "ok", "user": user, "message": "Account created successfully."}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(exc)}",
        )


@auth_router.post("/login")
def login(req: LoginRequest, request: Request, response: Response) -> dict[str, Any]:
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{req.email}"
    
    _check_rate_limit(rate_key)
    
    try:
        user_row = get_user_by_email(req.email)
        if not user_row or not verify_password(req.password, user_row["password_hash"]):
            _record_failed_attempt(rate_key)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )
            
        _clear_failed_attempts(rate_key)
        user = {"id": user_row["id"], "email": user_row["email"], "name": user_row["name"]}
        set_auth_cookie(response, user)
        return {"status": "ok", "user": user, "message": "Logged in successfully."}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(exc)}",
        )


@auth_router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"status": "ok", "message": "Logged out successfully."}


@auth_router.get("/me")
def me(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return {"authenticated": True, "user": current_user}
