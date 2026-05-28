"""
middleware/auth.py
──────────────────
JWT authentication dependencies for FastAPI route protection.

Usage
-----
    from backend.app.middleware.auth import (
        get_current_user,
        get_admin_user,
        get_counselor_or_admin,
        get_teacher_or_admin,
        get_faculty_or_admin,
    )

    @router.get("/protected")
    def endpoint(user: User = Depends(get_current_user)):
        ...
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.database import BlacklistedToken, User

logger = logging.getLogger(__name__)

# ── Password hashing ──────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return the bcrypt hash of *plain*."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return pwd_context.verify(plain, hashed)


# ── Token creation ────────────────────────────────────────────────────────────

def create_access_token(
    subject: str,
    role: str,
    extra: dict | None = None,
) -> tuple[str, int]:
    """
    Create a signed JWT access token.

    Returns
    -------
    (token_string, expires_in_seconds)
    """
    expire_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    expire         = datetime.now(timezone.utc) + timedelta(seconds=expire_seconds)

    payload = {
        "sub":  subject,
        "role": role,
        "type": "access",
        "exp":  expire,
        "iat":  datetime.now(timezone.utc),
        **(extra or {}),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, expire_seconds


def create_refresh_token(subject: str) -> tuple[str, str]:
    """
    Create a signed JWT refresh token.

    Returns
    -------
    (token_string, jti)   — jti is the unique token ID for blacklisting
    """
    import uuid
    jti    = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub":  subject,
        "type": "refresh",
        "jti":  jti,
        "exp":  expire,
        "iat":  datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


# ── Bearer scheme ─────────────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=True)


# ── Core dependency ───────────────────────────────────────────────────────────

def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db:          Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency.  Validates the Bearer token and returns the User row.

    Raises
    ------
    HTTPException 401  — invalid / expired / wrong-type token
    HTTPException 403  — account deactivated
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError as exc:
        logger.debug("JWT decode failed: %s", exc)
        raise credentials_exception from exc

    if payload.get("type") != "access":
        raise credentials_exception

    user_email: str | None = payload.get("sub")
    if not user_email:
        raise credentials_exception

    user = db.query(User).filter(User.email == user_email).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact your administrator.",
        )

    return user


# ── Role-based dependencies ───────────────────────────────────────────────────

def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the authenticated user to have role == 'admin'."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


def get_counselor_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the authenticated user to be counselor or admin."""
    if current_user.role not in ("admin", "counselor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Counselor or admin access required.",
        )
    return current_user


def get_teacher_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the authenticated user to be teacher or admin."""
    if current_user.role not in ("admin", "teacher"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher or admin access required.",
        )
    return current_user


def get_faculty_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the authenticated user to be faculty, counselor, teacher, or admin."""
    if current_user.role not in ("admin", "faculty", "counselor", "teacher"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faculty, counselor, teacher, or admin access required.",
        )
    return current_user


# ── Refresh-token validation (used in /refresh and /logout) ───────────────────

def decode_refresh_token(
    token: str,
    db:    Session,
) -> dict:
    """
    Decode and validate a refresh token.

    Raises
    ------
    HTTPException 401  — invalid, expired, wrong-type, or blacklisted token
    """
    bad_token = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token.",
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError as exc:
        logger.debug("Refresh token decode failed: %s", exc)
        raise bad_token from exc

    if payload.get("type") != "refresh":
        raise bad_token

    jti = payload.get("jti")
    if jti and db.query(BlacklistedToken).filter(BlacklistedToken.token_jti == jti).first():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
        )

    return payload
