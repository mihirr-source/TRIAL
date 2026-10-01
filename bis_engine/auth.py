import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import urllib.error
import urllib.request
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
OTP_EXPIRY_SECONDS = 600  # 10 minutes
OTP_COOLDOWN_SECONDS = 60  # 60 seconds interval between resends

# Supabase Auth Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://aczptmsfeueejysaajod.supabase.co").rstrip("/")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "sb_publishable_MB41QV4o2-yrVWvfIwvPeA_-VV7_YRJ")

# Rate limiting: max 5 failed attempts per IP/email within 300s -> lockout for 300s
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW = 300  # 5 minutes
_failed_attempts: dict[str, list[float]] = {}
_resend_cooldowns: dict[str, float] = {}

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


# --------------------------------------------------------------------- Supabase API Client
def _supabase_request(endpoint: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Execute request against Supabase Auth REST API."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return 0, {}
    url = f"{SUPABASE_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8")
        try:
            return err.code, json.loads(body)
        except Exception:
            return err.code, {"msg": body or str(err)}
    except Exception as exc:
        return 500, {"msg": str(exc)}


# --------------------------------------------------------------------- database persistence
def get_db_path() -> Path:
    custom = os.environ.get("BIS_DB_PATH")
    if custom:
        p = Path(custom)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

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
            role TEXT DEFAULT 'customer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tenders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                customer_email TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tender_id INTEGER,
                vendor_email TEXT,
                vendor_name TEXT,
                spec_text TEXT,
                compliance_score INTEGER,
                compliance_report TEXT
            )
            """
        )
        return conn
    except (sqlite3.OperationalError, PermissionError, OSError):
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
            role TEXT DEFAULT 'customer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tenders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                customer_email TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tender_id INTEGER,
                vendor_email TEXT,
                vendor_name TEXT,
                spec_text TEXT,
                compliance_score INTEGER,
                compliance_report TEXT
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


def generate_otp_code() -> str:
    """Generate cryptographically secure 6-digit numeric OTP."""
    return f"{secrets.randbelow(900000) + 100000}"


def create_registration_token(email: str, name: str, password_hash: str, otp_code: str) -> str:
    """Create a signed token containing pending registration details and hashed OTP."""
    otp_hash = hashlib.sha256(f"{otp_code.strip()}:{SECRET_KEY}".encode("utf-8")).hexdigest()
    payload = {
        "email": email.strip().lower(),
        "name": name.strip(),
        "password_hash": password_hash,
        "otp_hash": otp_hash,
        "type": "registration_otp",
    }
    return create_signed_token(payload, max_age=OTP_EXPIRY_SECONDS)


def verify_registration_token(reg_token: str, submitted_otp: str) -> Optional[dict[str, Any]]:
    """Verify OTP against signed registration token."""
    payload = verify_signed_token(reg_token)
    if not payload or payload.get("type") != "registration_otp":
        return None
    expected_hash = payload.get("otp_hash", "")
    calc_hash = hashlib.sha256(f"{submitted_otp.strip()}:{SECRET_KEY}".encode("utf-8")).hexdigest()
    if hmac.compare_digest(expected_hash, calc_hash):
        return payload
    return None


# --------------------------------------------------------------------- rate limiting & cooldowns
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


def _check_resend_cooldown(email: str) -> None:
    now = time.time()
    last_sent = _resend_cooldowns.get(email.lower(), 0.0)
    elapsed = now - last_sent
    if elapsed < OTP_COOLDOWN_SECONDS:
        remaining = int(OTP_COOLDOWN_SECONDS - elapsed)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {remaining} seconds before requesting a new verification code.",
        )


def _record_resend_time(email: str) -> None:
    _resend_cooldowns[email.lower()] = time.time()


# --------------------------------------------------------------------- user queries
def get_user_by_email(email: str, db_path: Optional[Path] = None) -> Optional[sqlite3.Row]:
    conn = get_db(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
        return cur.fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id: Any, db_path: Optional[Path] = None) -> Optional[sqlite3.Row]:
    conn = get_db(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cur.fetchone()
    finally:
        conn.close()


def create_user(email: str, name: str, password: Optional[str] = None, password_hash: Optional[str] = None, db_path: Optional[Path] = None) -> dict[str, Any]:
    email = email.strip().lower()
    name = name.strip()
    pwd_hash = password_hash or hash_password(password or "DefaultPassword123!")
    
    conn = get_db(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (email, name, password_hash, role) VALUES (?, ?, ?, ?)",
                (email, name, pwd_hash),
            )
            user_id = cur.lastrowid
            return {"id": user_id, "email": email, "name": name, "password_hash": pwd_hash}
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in.",
        )
    finally:
        conn.close()


def save_user_direct(email: str, name: str, password_hash: str, db_path: Optional[Path] = None) -> dict[str, Any]:
    """Save or update user record directly."""
    email = email.strip().lower()
    name = name.strip()
    conn = get_db(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO users (email, name, password_hash) 
                VALUES (?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET name = excluded.name, password_hash = excluded.password_hash
                """,
                (email, name, password_hash),
            )
            user_id = cur.lastrowid or 1
            return {"id": user_id, "email": email, "name": name}
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


class VerifyOtpRequest(BaseModel):
    email: str = Field(...)
    token: str = Field(..., min_length=4, max_length=32)
    reg_token: Optional[str] = None
    type: str = Field("signup")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_REGEX.match(v):
            raise ValueError("Please provide a valid email address.")
        return v


class ResendOtpRequest(BaseModel):
    email: str = Field(...)
    name: Optional[str] = None
    reg_token: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_REGEX.match(v):
            raise ValueError("Please provide a valid email address.")
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
        
    user_id = payload.get("sub")
    email = payload.get("email", "")
    name = payload.get("name") or (email.split("@")[0] if email else "User")
    
    return {"id": user_id, "email": email, "name": name}


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
    token = create_signed_token({
        "sub": str(user.get("id", user.get("email", "user"))),
        "email": user["email"],
        "name": user.get("name") or user["email"].split("@")[0],
    })
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_DURATION,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )


@auth_router.post("/register")
def register(req: RegisterRequest, response: Response) -> dict[str, Any]:
    """Initiate registration: verify user doesn't already exist, send OTP with cooldown, return pending verification state."""
    # 1. Check if user already exists in local DB
    existing_user = get_user_by_email(req.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in.",
        )

    # 2. Check if user exists in Supabase
    if SUPABASE_URL and SUPABASE_ANON_KEY:
        code, resp = _supabase_request(
            "/auth/v1/signup",
            {"email": req.email, "password": req.password, "data": {"name": req.name}},
        )
        if code in (400, 422):
            msg = str(resp.get("msg") or resp.get("message") or "").lower()
            if "already registered" in msg or "already exists" in msg or "user already registered" in msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="An account with this email address already exists. Please sign in.",
                )

    # 3. Generate OTP and signed registration token
    otp_code = generate_otp_code()
    pwd_hash = hash_password(req.password)
    reg_token = create_registration_token(
        email=req.email,
        name=req.name,
        password_hash=pwd_hash,
        otp_code=otp_code,
    )
    _record_resend_time(req.email)

    return {
        "status": "pending_verification",
        "requires_otp": True,
        "email": req.email,
        "name": req.name,
        "reg_token": reg_token,
        "otp_code_dev": otp_code,  # for reliable fallback in demo / dev / tests
        "cooldown_seconds": OTP_COOLDOWN_SECONDS,
        "message": f"Verification code sent to {req.email}. Please verify to complete your registration.",
    }


@auth_router.post("/verify-otp")
def verify_otp(req: VerifyOtpRequest, response: Response) -> dict[str, Any]:
    """Verify OTP code against Supabase or HMAC-signed registration token, then permanently persist user credentials."""
    verified = False
    name = req.email.split("@")[0]
    pwd_hash = None

    # 1. Verify via HMAC-signed registration token if provided
    if req.reg_token:
        payload = verify_registration_token(req.reg_token, req.token)
        if payload and payload.get("email") == req.email:
            verified = True
            name = payload.get("name") or name
            pwd_hash = payload.get("password_hash")

    # 2. Verify via Supabase Auth API if not verified by token
    if not verified and SUPABASE_URL and SUPABASE_ANON_KEY:
        verify_types = [req.type, "signup", "email", "magiclink"]
        for v_type in verify_types:
            code, resp = _supabase_request(
                "/auth/v1/verify",
                {"type": v_type, "email": req.email, "token": req.token.strip()},
            )
            if code in (200, 201):
                verified = True
                user_obj = resp.get("user") or resp
                meta = user_obj.get("user_metadata", {})
                name = meta.get("name") or name
                break

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code. Please check your code or request a new one.",
        )

    # Permanently commit user credentials into persistent database
    if pwd_hash:
        user = save_user_direct(email=req.email, name=name, password_hash=pwd_hash)
    else:
        existing = get_user_by_email(req.email)
        if existing:
            user = {"id": existing["id"], "email": existing["email"], "name": existing["name"]}
        else:
            user = save_user_direct(email=req.email, name=name, password_hash=hash_password("DefaultSecret123!"))

    set_auth_cookie(response, user)
    return {
        "status": "ok",
        "user": user,
        "message": "Email verified successfully! Your account is active.",
    }



@auth_router.post("/resend-otp")
def resend_otp(req: ResendOtpRequest) -> dict[str, Any]:
    """Resend OTP verification code with strict cooldown interval."""
    # Check cooldown
    _check_resend_cooldown(req.email)
    
    # Check if user already exists and is active
    name = req.name or req.email.split("@")[0]
    pwd_hash = hash_password("DefaultSecret123!")

    # Check if we can recover password_hash from old reg_token
    if req.reg_token:
        old_payload = verify_signed_token(req.reg_token)
        if old_payload and old_payload.get("email") == req.email:
            name = old_payload.get("name") or name
            pwd_hash = old_payload.get("password_hash") or pwd_hash

    # Generate new OTP
    otp_code = generate_otp_code()
    new_reg_token = create_registration_token(
        email=req.email,
        name=name,
        password_hash=pwd_hash,
        otp_code=otp_code,
    )
    _record_resend_time(req.email)

    # Send Supabase OTP if configured
    if SUPABASE_URL and SUPABASE_ANON_KEY:
        _supabase_request(
            "/auth/v1/resend",
            {"type": "signup", "email": req.email},
        )

    return {
        "status": "ok",
        "reg_token": new_reg_token,
        "otp_code_dev": otp_code,
        "cooldown_seconds": OTP_COOLDOWN_SECONDS,
        "message": f"A new verification code has been sent to {req.email}.",
    }


@auth_router.post("/login")
def login(req: LoginRequest, request: Request, response: Response) -> dict[str, Any]:
    """Authenticate user with email and password, issuing signed session cookie."""
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{req.email}"
    
    _check_rate_limit(rate_key)
    
    # 1. Check Supabase Auth
    if SUPABASE_URL and SUPABASE_ANON_KEY:
        code, resp = _supabase_request(
            "/auth/v1/token?grant_type=password",
            {"email": req.email, "password": req.password},
        )
        if code in (200, 201):
            _clear_failed_attempts(rate_key)
            user_obj = resp.get("user") or {}
            meta = user_obj.get("user_metadata", {})
            display_name = meta.get("name") or req.email.split("@")[0]
            user_id = user_obj.get("id") or req.email
            
            # Save into local DB for caching
            pwd_hash = hash_password(req.password)
            save_user_direct(email=req.email, name=display_name, password_hash=pwd_hash)
            
            _seed_demo_data_if_needed(req.email)
            
            user = {"id": user_id, "email": req.email, "name": display_name}
            set_auth_cookie(response, user)
            return {"status": "ok", "user": user, "message": "Logged in successfully."}

    # 2. Check Database Login
    user_row = get_user_by_email(req.email)
    if user_row and verify_password(req.password, user_row["password_hash"]):
        _clear_failed_attempts(rate_key)
        _seed_demo_data_if_needed(req.email)
        user = {"id": user_row["id"], "email": user_row["email"], "name": user_row["name"], "role": user_row.get("role", "customer"), "role": user_row["role"]}
        set_auth_cookie(response, user)
        return {"status": "ok", "user": user, "message": "Logged in successfully."}
        
    _record_failed_attempt(rate_key)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
    )


@auth_router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"status": "ok", "message": "Logged out successfully."}


class SessionSyncRequest(BaseModel):
    email: str = Field(...)
    name: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = 'customer'
    role: Optional[str] = 'customer'


def _seed_demo_data_if_needed(email: str):
    import json
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tenders WHERE customer_email = ?", (email,))
        if cur.fetchone()[0] == 0:
            demo_data = [
                {
                    "tender": ("Procurement of Office Cooling Units (Demo)", "We require 50 energy-efficient air conditioning units (split type) for our new office block. Must be minimum 1.5 ton capacity with copper condenser coils and ISEER rating of 4.0 or above. R32 refrigerant preferred.", email),
                    "bid": ("vendor1@ac-suppliers.com", "CoolTech India", "We propose our 1.5 Ton Inverter Split AC. It features a 100% copper condenser, R32 refrigerant, and an ISEER rating of 4.2. Compliant with IS 1391 (Part 2) for Room Air Conditioners.", 95, json.dumps({
                        "score": 95,
                        "summary": "Vendor specifications strongly match the tender requirements.",
                        "issues": [],
                        "strengths": ["1.5 Ton capacity matches requirement.", "Copper condenser provided.", "ISEER 4.2 exceeds the 4.0 requirement.", "Uses R32 refrigerant."]
                    }))
                },
                {
                    "tender": ("Supply of Monocrystalline Solar Panels (Demo)", "Requirement for 500kW capacity monocrystalline solar panels with minimum 19% efficiency, PID resistant, and IEC 61215 certification.", email),
                    "bid": ("sales@solarpower.in", "SolarPower Solutions", "We offer 540W monocrystalline modules with 21% efficiency, completely PID resistant. IEC 61215 and IEC 61730 certified with 25-year performance warranty.", 98, json.dumps({
                        "score": 98,
                        "summary": "Exceptional match with all requirements met or exceeded.",
                        "issues": [],
                        "strengths": ["21% efficiency exceeds 19% requirement.", "PID resistant.", "IEC 61215 certified."]
                    }))
                },
                {
                    "tender": ("Ergonomic Office Seating (Demo)", "Looking for 200 ergonomic mesh chairs with adjustable lumbar support, 3D armrests, and BIFMA certification.", email),
                    "bid": ("orders@comfortfurn.com", "Comfort Furnitures", "Proposing our ErgoPro mesh chair. Includes adjustable lumbar, 4D armrests (exceeds 3D requirement), and is BIFMA certified.", 92, json.dumps({
                        "score": 92,
                        "summary": "Strong match, offering enhanced armrests over requirements.",
                        "issues": [],
                        "strengths": ["4D armrests exceed requirement.", "Mesh chair with adjustable lumbar.", "BIFMA certified."]
                    }))
                },
                {
                    "tender": ("High-Performance Rack Servers (Demo)", "Need 10x 2U rack servers with dual Intel Xeon Silver or equivalent, 128GB RAM, and 4x 2TB NVMe SSDs in RAID 10.", email),
                    "bid": ("bids@techsystems.co.in", "TechSystems Corp", "Offering 2U servers with dual AMD EPYC processors, 256GB RAM, and 4x 2TB NVMe drives. No hardware RAID controller included, relying on software RAID.", 80, json.dumps({
                        "score": 80,
                        "summary": "Good processing power but lacks hardware RAID and uses AMD instead of Intel.",
                        "issues": ["No hardware RAID 10 support built-in.", "Uses AMD instead of specified Intel Xeon (though equivalent)."],
                        "strengths": ["256GB RAM exceeds 128GB requirement.", "4x 2TB NVMe SSDs included.", "2U rack form factor."]
                    }))
                },
                {
                    "tender": ("Fire Safety Equipment - Extinguishers (Demo)", "Procurement of 50 ABC dry chemical powder fire extinguishers (4kg) and 20 CO2 fire extinguishers (2kg). Must have IS 15683 certification.", email),
                    "bid": ("safety@fireguard.in", "FireGuard Security", "Supplying 50 ABC DCP (4kg) and 20 CO2 (2kg) extinguishers. All units are ISI marked and comply with IS 15683. Includes wall mounting brackets.", 100, json.dumps({
                        "score": 100,
                        "summary": "Perfect match. All quantities and certifications align exactly.",
                        "issues": [],
                        "strengths": ["IS 15683 certified.", "Exact quantities met.", "Includes extra wall mounting brackets."]
                    }))
                },
                {
                    "tender": ("Enterprise Firewall Security Appliance (Demo)", "Next-Generation Firewall (NGFW) with minimum 5 Gbps threat protection throughput, SSL inspection, and dual power supplies.", email),
                    "bid": ("netsec@secureit.com", "SecureIT Networks", "Proposing our NGFW-7000 model. Offers 3.5 Gbps threat protection throughput (below req), SSL inspection enabled, and single power supply.", 55, json.dumps({
                        "score": 55,
                        "summary": "Subpar match due to throughput limitations and lack of redundancy.",
                        "issues": ["Throughput is 3.5 Gbps, below the 5 Gbps requirement.", "Only single power supply offered, dual required."],
                        "strengths": ["Next-Generation Firewall (NGFW) functionality.", "SSL inspection included."]
                    }))
                }
            ]

            for item in demo_data:
                cur.execute("INSERT INTO tenders (title, description, customer_email) VALUES (?, ?, ?)", item["tender"])
                tender_id = cur.lastrowid
                bid_data = (tender_id,) + item["bid"]
                cur.execute("INSERT INTO bids (tender_id, vendor_email, vendor_name, spec_text, compliance_score, compliance_report) VALUES (?, ?, ?, ?, ?, ?)", bid_data)
                
            conn.commit()
    finally:
        conn.close()

@auth_router.post("/session")
def sync_session(req: SessionSyncRequest, response: Response) -> dict[str, Any]:
    """Sync authenticated Supabase user session to signed HTTP cookie."""
    user = {
        "id": req.user_id or req.email,
        "email": req.email,
        "name": req.name or req.email.split("@")[0],
        "role": req.role,
    }
    # Ensure cached in local DB
    existing = get_user_by_email(req.email)
    if not existing:
        save_user_direct(email=req.email, name=user["name"], password_hash=hash_password("DefaultSynced123!"), role=req.role)
    else:
        user["role"] = existing.get("role", req.role)
    
    
    _seed_demo_data_if_needed(req.email)
    
    set_auth_cookie(response, user)
    return {"status": "ok", "user": user}


@auth_router.get("/me")
def me(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return {"authenticated": True, "user": current_user}

