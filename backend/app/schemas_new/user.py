"""
schemas/user.py
───────────────
Pydantic schemas for user-related endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str | None = None
    role: Literal["admin", "faculty"] = "faculty"
    institute_id: int | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None
    role: str
    institute_id: int | None
    is_active: bool
    created_at: datetime
    last_login: datetime | None

    model_config = {"from_attributes": True}


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8)
