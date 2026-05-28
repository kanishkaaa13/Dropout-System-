"""
schemas/student.py
─────────────────
Pydantic schemas for student-related endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class StudentCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr | None = None
    phone: str | None = None
    batch_id: int | None = None
    assigned_faculty_id: int | None = None
    enrollment_date: datetime | None = None
    target_rank: int | None = None
    target_college: str | None = None
    is_demo: bool = False


class StudentUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    batch_id: int | None = None
    assigned_faculty_id: int | None = None
    target_rank: int | None = None
    target_college: str | None = None
    is_active: bool | None = None


class StudentResponse(BaseModel):
    id: int
    student_code: str | None
    full_name: str
    email: str | None
    phone: str | None
    batch_id: int | None
    assigned_faculty_id: int | None
    enrollment_date: datetime | None
    target_rank: int | None
    target_college: str | None
    is_active: bool
    is_demo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StudentListResponse(BaseModel):
    students: list[StudentResponse]
    total: int
    page: int
    page_size: int
