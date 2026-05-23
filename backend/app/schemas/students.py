"""
schemas/students.py
───────────────────
Pydantic schemas for student CRUD and related endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── MockTestResult ────────────────────────────────────────────────────────────

class MockTestCreate(BaseModel):
    test_date:        datetime
    test_name:        Optional[str] = None
    test_type:        Optional[str] = Field(None, pattern="^(minor|major|grand_test)$")
    total_score:      float = Field(..., ge=0, le=360)
    physics_score:    Optional[float] = Field(None, ge=0, le=120)
    chemistry_score:  Optional[float] = Field(None, ge=0, le=120)
    maths_score:      Optional[float] = Field(None, ge=0, le=120)
    percentile:       Optional[float] = Field(None, ge=0, le=100)
    rank_in_batch:    Optional[int]   = Field(None, ge=1)


class MockTestOut(MockTestCreate):
    id:         int
    student_id: int

    model_config = {"from_attributes": True}


# ── WeeklySurvey ──────────────────────────────────────────────────────────────

class SurveyCreate(BaseModel):
    burnout_score:          int   = Field(..., ge=1, le=10)
    stress_level:           int   = Field(..., ge=1, le=10)
    sleep_hours_avg:        float = Field(..., ge=3, le=12)
    study_hours_per_day:    float = Field(..., ge=0, le=16)
    parental_pressure:      int   = Field(..., ge=1, le=10)
    peer_comparison_stress: int   = Field(..., ge=1, le=10)
    motivation_level:       Optional[int]   = Field(None, ge=1, le=10)
    notes:                  Optional[str]   = None


class SurveyOut(SurveyCreate):
    id:          int
    student_id:  int
    survey_date: datetime
    week_number: Optional[int]

    model_config = {"from_attributes": True}


# ── Student ───────────────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    full_name:           str = Field(..., min_length=2, max_length=200)
    email:               Optional[EmailStr] = None
    phone:               Optional[str]      = None
    batch_id:            Optional[int]      = None
    assigned_faculty_id: Optional[int]      = None
    enrollment_date:     Optional[datetime] = None
    target_rank:         Optional[int]      = Field(None, ge=1)
    target_college:      Optional[str]      = None
    student_code:        Optional[str]      = None


class StudentUpdate(BaseModel):
    full_name:           Optional[str]      = None
    email:               Optional[EmailStr] = None
    phone:               Optional[str]      = None
    batch_id:            Optional[int]      = None
    assigned_faculty_id: Optional[int]      = None
    target_rank:         Optional[int]      = None
    target_college:      Optional[str]      = None
    is_active:           Optional[bool]     = None


class RiskSummary(BaseModel):
    risk_score:  Optional[float]
    risk_level:  Optional[str]
    assessed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class StudentOut(BaseModel):
    id:                  int
    student_code:        Optional[str]
    full_name:           str
    email:               Optional[str]
    phone:               Optional[str]
    batch_id:            Optional[int]
    assigned_faculty_id: Optional[int]
    enrollment_date:     Optional[datetime]
    target_rank:         Optional[int]
    target_college:      Optional[str]
    is_active:           bool
    created_at:          datetime
    latest_risk:         Optional[RiskSummary] = None

    model_config = {"from_attributes": True}


class StudentListResponse(BaseModel):
    items:   list[StudentOut]
    total:   int
    page:    int
    size:    int
    pages:   int


# ── RiskHistory ───────────────────────────────────────────────────────────────

class RiskHistoryPoint(BaseModel):
    assessed_at:    datetime
    risk_score:     Optional[float]
    risk_level:     Optional[str]
    ml_probability: Optional[float]

    model_config = {"from_attributes": True}
