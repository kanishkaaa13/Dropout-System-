"""
routers/auth.py
───────────────
Authentication endpoints:
  POST /auth/login
  POST /auth/refresh
  POST /auth/logout
  GET  /auth/me
  PUT  /auth/change-password
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.middleware.auth import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.app.models.database import BlacklistedToken, User
from backend.app.schemas.auth import (
    AccessTokenResponse,
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    TokenResponse,
    UserProfile,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── POST /auth/login ──────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
)
def login(
    body: LoginRequest,
    db:   Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate a user and return JWT access + refresh tokens.

    - **email**: registered email address
    - **password**: plaintext password (min 6 chars)
    """
    user = db.query(User).filter(User.email == body.email).first()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact your administrator.",
        )

    access_token,  expires_in = create_access_token(user.email, user.role)
    refresh_token, _jti       = create_refresh_token(user.email)

    # Update last_login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    logger.info("User %s logged in (role=%s).", user.email, user.role)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
    )


# ── POST /auth/refresh ────────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Exchange a refresh token for a new access token",
)
def refresh(
    body: RefreshRequest,
    db:   Session = Depends(get_db),
) -> AccessTokenResponse:
    """
    Validate a refresh token and issue a new short-lived access token.
    The refresh token is NOT rotated (stateless; use /logout to invalidate).
    """
    payload = decode_refresh_token(body.refresh_token, db)

    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated.",
        )

    access_token, expires_in = create_access_token(user.email, user.role)

    return AccessTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )


# ── POST /auth/logout ─────────────────────────────────────────────────────────

@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke a refresh token",
)
def logout(
    body: RefreshRequest,
    db:   Session = Depends(get_db),
) -> MessageResponse:
    """
    Blacklist the provided refresh token so it can no longer be used.
    The caller should also discard the access token client-side.
    """
    from datetime import datetime as _dt, timezone as _tz
    from jose import jwt as _jwt, JWTError
    from backend.app.config import settings as _s

    try:
        payload = _jwt.decode(
            body.refresh_token, _s.SECRET_KEY, algorithms=[_s.ALGORITHM]
        )
        jti        = payload.get("jti")
        exp_ts     = payload.get("exp")
        expires_at = _dt.fromtimestamp(exp_ts, tz=_tz.utc) if exp_ts else None
    except JWTError:
        # Even if the token is invalid/expired, treat logout as success
        return MessageResponse(message="Logged out successfully.")

    if jti:
        existing = db.query(BlacklistedToken).filter(BlacklistedToken.token_jti == jti).first()
        if not existing:
            db.add(BlacklistedToken(token_jti=jti, expires_at=expires_at))
            db.commit()

    logger.info("Refresh token (jti=%s) blacklisted.", jti)
    return MessageResponse(message="Logged out successfully.")


# ── GET /auth/me ──────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserProfile,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the profile of the currently authenticated user."""
    return current_user


# ── PUT /auth/change-password ─────────────────────────────────────────────────

@router.put(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change the current user's password",
)
def change_password(
    body:         ChangePasswordRequest,
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db),
) -> MessageResponse:
    """
    Verify the old password, then store the new bcrypt hash.

    - **old_password**: current password for verification
    - **new_password**: new password (min 8 chars)
    """
    if not verify_password(body.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect.",
        )

    if body.new_password == body.old_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must differ from the old password.",
        )

    current_user.hashed_password = hash_password(body.new_password)
    db.commit()

    logger.info("User %s changed their password.", current_user.email)
    return MessageResponse(message="Password updated successfully.")
