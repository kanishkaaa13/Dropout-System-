"""
schemas/auth.py
───────────────
Pydantic schemas for authentication endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# ── Request schemas ───────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str = Field(..., min_length=6)


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8)


# ── Response schemas ──────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int          # seconds until access token expiry


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int


class UserProfile(BaseModel):
    id:           int
    email:        EmailStr
    full_name:    str | None
    role:         str
    institute_id: int | None
    is_active:    bool
    created_at:   datetime
    last_login:   datetime | None

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str
    success: bool = True
