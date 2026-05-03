"""auth_service.py — Core authentication helpers.

Responsibilities
────────────────
- Password hashing/verification (bcrypt via passlib)
- JWT creation & decoding (PyJWT)
- TOTP generation & verification (pyotp)
- Device fingerprinting & suspicious-IP detection
- JWT blacklist via Redis (logout)
- Email OTP for device verification
- Password reset tokens
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
import pyotp
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import DeviceVerificationCode, PasswordResetToken, User, UserSession

# ── Password hashing ──────────────────────────────────────────────────────────

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(
    user_id: UUID,
    org_id: UUID | None,
    role: str,
    plan: str,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=settings.jwt_access_token_expire_hours)
    payload: dict = {
        "sub": str(user_id),
        "org_id": str(org_id) if org_id else None,
        "role": role,
        "plan": plan,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Raises jwt.InvalidTokenError (or subclass) on invalid/expired token."""
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["sub", "exp", "iat"]},
    )


def get_current_user_id(token: str) -> UUID | None:
    """Convenience helper — returns user UUID from a decoded token or None."""
    try:
        data = decode_access_token(token)
        return UUID(data["sub"])
    except Exception:
        return None


# ── TOTP ──────────────────────────────────────────────────────────────────────

def generate_totp_secret() -> str:
    return pyotp.random_base32()


def verify_totp(secret: str, code: str) -> bool:
    """Accept current and adjacent window (±30 s) to tolerate clock skew."""
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def get_totp_provisioning_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(
        name=email, issuer_name=settings.totp_issuer
    )


# ── Device fingerprinting ─────────────────────────────────────────────────────

def fingerprint_ip(ip: str, user_agent: str = "") -> str:
    """Returns a SHA-256 hex of IP + User-Agent. Safe to persist."""
    raw = f"{ip}:{user_agent}"
    return hashlib.sha256(raw.encode()).hexdigest()


def is_suspicious_ip(db: Session, user_id: UUID, ip_hash: str) -> bool:
    """True when the IP hash has never been seen in the 30 most-recent sessions.
    Returns False on the very first login (no baseline yet)."""
    rows = db.execute(
        select(UserSession.ip_hash)
        .where(UserSession.user_id == user_id)
        .order_by(UserSession.created_at.desc())
        .limit(30)
    ).scalars().all()
    if not rows:
        return False  # first-ever login → trust
    return ip_hash not in rows


def record_session(db: Session, user_id: UUID, ip_hash: str, user_agent: str) -> None:
    db.add(UserSession(user_id=user_id, ip_hash=ip_hash, user_agent=user_agent[:255]))
    db.commit()


# ── JWT blacklist (Redis) ─────────────────────────────────────────────────────

def _redis_client():
    import redis as _r
    return _r.from_url(settings.redis_url, decode_responses=True)


def blacklist_token(token: str, ttl_seconds: int) -> None:
    try:
        _redis_client().setex(f"bl:{token}", max(ttl_seconds, 1), "1")
    except Exception:
        pass  # Non-fatal — Redis outage won't block logout flow


def is_token_blacklisted(token: str) -> bool:
    try:
        return _redis_client().exists(f"bl:{token}") > 0
    except Exception:
        return False  # Fail open on Redis outage


# ── Device verification codes (email OTP for suspicious logins) ───────────────

def generate_device_code(db: Session, user_id: UUID) -> str:
    """Creates a new 6-digit code, invalidates any existing ones for this user.
    Returns the plaintext code (caller must send it by email)."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    now = datetime.now(timezone.utc)
    # Purge existing codes for this user
    existing = db.execute(
        select(DeviceVerificationCode).where(DeviceVerificationCode.user_id == user_id)
    ).scalars().all()
    for row in existing:
        db.delete(row)
    dvc = DeviceVerificationCode(
        user_id=user_id,
        code=hashlib.sha256(code.encode()).hexdigest(),
        expires_at=now + timedelta(minutes=10),
    )
    db.add(dvc)
    db.commit()
    return code


def verify_device_code(db: Session, user_id: UUID, code: str) -> bool:
    """Returns True and deletes the row if code is valid & not expired."""
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    row = db.execute(
        select(DeviceVerificationCode).where(
            DeviceVerificationCode.user_id == user_id,
            DeviceVerificationCode.code == code_hash,
            DeviceVerificationCode.expires_at > datetime.now(timezone.utc),
        )
    ).scalar_one_or_none()
    if row:
        db.delete(row)
        db.commit()
        return True
    return False


# ── Password reset tokens ─────────────────────────────────────────────────────

_RESET_TTL_HOURS = 1


def generate_reset_token(db: Session, user_id: UUID) -> str:
    """Creates a 1-hour reset token. Returns the plaintext token (for email link)."""
    token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now = datetime.now(timezone.utc)
    # Invalidate existing tokens for the user
    existing = db.execute(
        select(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
    ).scalars().all()
    for row in existing:
        db.delete(row)
    prt = PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=now + timedelta(hours=_RESET_TTL_HOURS),
    )
    db.add(prt)
    db.commit()
    return token


def consume_reset_token(db: Session, token: str) -> UUID | None:
    """Returns the user_id if valid, marks token as used. Returns None if invalid."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    row = db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
            PasswordResetToken.used_at.is_(None),
        )
    ).scalar_one_or_none()
    if not row:
        return None
    row.used_at = datetime.now(timezone.utc)
    db.commit()
    return row.user_id


# ── Account lockout helpers ───────────────────────────────────────────────────

def record_failed_attempt(db: Session, user: User) -> None:
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
    if user.failed_login_attempts >= settings.login_max_attempts:
        user.locked_until = datetime.now(timezone.utc) + timedelta(
            minutes=settings.login_lockout_minutes
        )
    db.commit()


def reset_failed_attempts(db: Session, user: User) -> None:
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()


def is_account_locked(user: User) -> bool:
    if not user.locked_until:
        return False
    return user.locked_until > datetime.now(timezone.utc)


# ── Pending auth state (MFA/device check mid-flow) ───────────────────────────

_PENDING_COOKIE = "pending_auth"
_PENDING_TTL = 600  # 10 minutes


def encode_pending_state(
    user_id: UUID, org_id: UUID | None, role: str, plan: str, mfa_type: str
) -> str:
    """Creates a signed, time-limited string for the pending_auth cookie."""
    from itsdangerous import URLSafeTimedSerializer
    s = URLSafeTimedSerializer(settings.jwt_secret_key)
    return s.dumps({
        "user_id": str(user_id),
        "org_id": str(org_id) if org_id else None,
        "role": role,
        "plan": plan,
        "mfa_type": mfa_type,  # "totp" | "device"
    })


def decode_pending_state(signed: str) -> dict | None:
    """Returns the dict or None if expired/invalid."""
    from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
    s = URLSafeTimedSerializer(settings.jwt_secret_key)
    try:
        return s.loads(signed, max_age=_PENDING_TTL)
    except (BadSignature, SignatureExpired):
        return None
