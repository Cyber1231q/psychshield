"""Authentication router — handles user registration and login.

Endpoints:
    POST /api/auth/register — Create a new user account.
    POST /api/auth/login    — Authenticate and return a JWT token.
"""

import hashlib
import hmac
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from models.database import get_db
from models.entities import AuditLog, PasswordResetToken, User
from utils import rate_limiter
import urllib.request
import json as json_mod

from models.schemas import (
    ForgotPasswordRequest,
    GoogleAuthRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    ValidateTokenRequest,
)

logger = logging.getLogger("psychshield")

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

JWT_SECRET: str = os.getenv("JWT_SECRET", "")
if not JWT_SECRET:
    import secrets

    JWT_SECRET = secrets.token_hex(32)
    logger.warning(
        "JWT_SECRET not set — generated ephemeral secret. "
        "Set JWT_SECRET in .env for persistent sessions."
    )

JWT_ALGORITHM: str = "HS256"
JWT_EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "8"))

# ── A04: Rate limiting for brute-force protection ───────────────
# Backed by Redis when REDIS_URL is set (shared across instances), an
# in-memory dict otherwise — see utils/rate_limiter.py.

_MAX_LOGIN_ATTEMPTS: int = 5
_MAX_GENERAL_ATTEMPTS: int = 15
_WINDOW_SECONDS: int = 300


def _check_rate_limit(identifier: str) -> None:
    """Block if too many attempts in _WINDOW_SECONDS."""
    is_login = not identifier.startswith(("register:", "google:"))
    limit = _MAX_LOGIN_ATTEMPTS if is_login else _MAX_GENERAL_ATTEMPTS
    rate_limiter.check(identifier, limit, _WINDOW_SECONDS)


def _record_attempt(identifier: str) -> None:
    """Record a login attempt timestamp."""
    rate_limiter.record(identifier, _WINDOW_SECONDS)


# ── Password helpers ────────────────────────────────────────────

def _hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── Token helpers ───────────────────────────────────────────────

def create_token(data: dict) -> str:
    """Create a signed JWT with an expiration claim."""
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency — decode and validate the Bearer token."""
    try:
        payload: dict = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if "sub" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return payload
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """FastAPI dependency — reject non-admin users with 403."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ── Audit helper ────────────────────────────────────────────────

def _log_audit(db: Session, actor: str, action: str) -> None:
    """Write an entry to the audit log."""
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        actor=actor,
        action=action,
        timestamp=datetime.now(timezone.utc),
    ))
    db.commit()


# ── Routes ──────────────────────────────────────────────────────

@router.post("/auth/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    req: Request,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Authenticate a user and return a JWT token."""
    client_ip = req.client.host if req.client else "unknown"
    rate_key = f"{client_ip}:{request.email}"
    _check_rate_limit(rate_key)
    _record_attempt(rate_key)

    user: User | None = db.query(User).filter(User.email == request.email).first()
    if not user or not _verify_password(request.password, user.password_hash):
        _log_audit(db, request.email, f"Failed login attempt from {client_ip}")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    rate_limiter.clear(rate_key)

    token = create_token({"sub": user.email, "role": user.role, "name": user.name})
    _log_audit(db, user.email, "Login successful")

    return LoginResponse(
        token=token,
        user={"email": user.email, "role": user.role, "name": user.name},
    )


@router.post("/auth/register", response_model=LoginResponse)
def register(
    request: RegisterRequest, req: Request, db: Session = Depends(get_db)
) -> LoginResponse:
    """Create a new user account and return a JWT token."""
    client_ip = req.client.host if req.client else "unknown"
    _check_rate_limit(f"register:{client_ip}")
    _record_attempt(f"register:{client_ip}")

    existing: User | None = (
        db.query(User).filter(User.email == request.email).first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(
        id=str(uuid.uuid4()),
        email=request.email,
        password_hash=_hash_password(request.password),
        role="analyst",
        name=request.name,
        status="active",
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_user)
    db.commit()

    token = create_token(
        {"sub": new_user.email, "role": new_user.role, "name": new_user.name}
    )
    _log_audit(db, new_user.email, "New account registered")

    return LoginResponse(
        token=token,
        user={"email": new_user.email, "role": new_user.role, "name": new_user.name},
    )


GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")


@router.post("/auth/google", response_model=LoginResponse)
def google_auth(
    request: GoogleAuthRequest, req: Request, db: Session = Depends(get_db)
) -> LoginResponse:
    """Authenticate or register a user via Google OAuth ID token."""
    client_ip = req.client.host if req.client else "unknown"
    _check_rate_limit(f"google:{client_ip}")
    _record_attempt(f"google:{client_ip}")

    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={request.credential}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            payload = json_mod.loads(resp.read())
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google credential")

    if GOOGLE_CLIENT_ID and payload.get("aud") != GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=401, detail="Google token audience mismatch")

    if payload.get("email_verified") != "true":
        raise HTTPException(status_code=401, detail="Google email not verified")

    google_email = payload.get("email", "").lower()
    google_name = payload.get("name", google_email.split("@")[0])

    if not google_email:
        raise HTTPException(status_code=401, detail="No email in Google token")

    user = db.query(User).filter(User.email == google_email).first()

    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email=google_email,
            password_hash=_hash_password(secrets.token_urlsafe(32)),
            role="analyst",
            name=google_name,
            status="active",
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        _log_audit(db, google_email, "Account created via Google OAuth")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_token({"sub": user.email, "role": user.role, "name": user.name})
    _log_audit(db, user.email, "Login via Google OAuth")

    return LoginResponse(
        token=token,
        user={"email": user.email, "role": user.role, "name": user.name},
    )


# ── Password reset helpers ─────────────────────────────────────

_RESET_RATE_LIMIT_WINDOW: int = 300
_RESET_RATE_LIMIT_MAX: int = 3


def _check_reset_rate_limit(email: str) -> bool:
    """Return True if allowed, False if rate-limited."""
    key = f"reset:{email.lower().strip()}"
    if not rate_limiter.check_bool(key, _RESET_RATE_LIMIT_MAX, _RESET_RATE_LIMIT_WINDOW):
        return False
    rate_limiter.record(key, _RESET_RATE_LIMIT_WINDOW)
    return True


def _hash_token(token: str) -> str:
    """Hash a reset token with SHA-256 before storing."""
    return hashlib.sha256(token.encode()).hexdigest()


def _verify_token_hash(token: str, stored_hash: str) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    return hmac.compare_digest(
        hashlib.sha256(token.encode()).hexdigest(),
        stored_hash,
    )


# ── Password reset routes ──────────────────────────────────────

@router.post("/auth/forgot-password", response_model=MessageResponse)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Initiate password reset. Always returns the same message
    regardless of whether the email exists (prevents enumeration)."""
    email = request.email.lower().strip()
    safe_msg = MessageResponse(
        message="If an account exists with this email, a password reset link has been generated."
    )

    if not _check_reset_rate_limit(email):
        return safe_msg

    user = db.query(User).filter(User.email == email).first()

    if user:
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_email == email,
            PasswordResetToken.used == False,  # noqa: E712
        ).update({"used": True})

        raw_token = secrets.token_urlsafe(32)

        reset_entry = PasswordResetToken(
            id=str(uuid.uuid4()),
            user_email=email,
            token_hash=_hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            used=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(reset_entry)
        _log_audit(db, email, f"Password reset requested for {email}")

        from utils.email_sender import is_smtp_configured, send_reset_email

        if is_smtp_configured():
            send_reset_email(email, raw_token)
        else:
            logger.info("PASSWORD RESET TOKEN for %s: %s", email, raw_token)
            logger.info(
                "Reset link: http://localhost:5173/reset-password?token=%s",
                raw_token,
            )

    return safe_msg


@router.post("/auth/reset-password", response_model=MessageResponse)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Complete password reset with a one-time token."""
    import re as _re

    new_pw = request.new_password
    errors: list[str] = []
    if len(new_pw) < 8:
        errors.append("at least 8 characters")
    if not _re.search(r"[A-Z]", new_pw):
        errors.append("at least one uppercase letter")
    if not _re.search(r"[a-z]", new_pw):
        errors.append("at least one lowercase letter")
    if not _re.search(r"\d", new_pw):
        errors.append("at least one digit")
    if not _re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:'\",.<>?/\\`~]", new_pw):
        errors.append("at least one special character")
    if errors:
        raise HTTPException(
            status_code=400,
            detail="Password must contain: " + ", ".join(errors),
        )

    stored_tokens = db.query(PasswordResetToken).filter(
        PasswordResetToken.used == False,  # noqa: E712
        PasswordResetToken.expires_at > datetime.now(timezone.utc),
    ).all()

    matched_token = None
    for stored in stored_tokens:
        if _verify_token_hash(request.token, stored.token_hash):
            matched_token = stored
            break

    if not matched_token:
        _log_audit(db, "unknown", "Failed password reset attempt - invalid or expired token")
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token. Please request a new one.",
        )

    matched_token.used = True

    user = db.query(User).filter(User.email == matched_token.user_email).first()
    if user:
        user.password_hash = _hash_password(new_pw)
        _log_audit(db, user.email, f"Password reset completed for {user.email}")

    db.commit()

    return MessageResponse(
        message="Password has been reset successfully. You can now sign in with your new password."
    )


@router.post("/auth/validate-reset-token", response_model=MessageResponse)
def validate_reset_token(
    request: ValidateTokenRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Check if a reset token is still valid before showing the form."""
    token = request.token

    stored_tokens = db.query(PasswordResetToken).filter(
        PasswordResetToken.used == False,  # noqa: E712
        PasswordResetToken.expires_at > datetime.now(timezone.utc),
    ).all()

    for stored in stored_tokens:
        if _verify_token_hash(token, stored.token_hash):
            return MessageResponse(message="Token is valid")

    raise HTTPException(status_code=400, detail="Invalid or expired token")
