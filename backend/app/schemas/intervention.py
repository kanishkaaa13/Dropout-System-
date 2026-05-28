"""
schemas/intervention.py
──────────────────────
Pydantic schemas for intervention endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Action item schema ─────────────────────────────────────────────────────────

class ActionItem(BaseModel):
    type: str = Field(..., description="Type of action: counseling, academic, wellness")
    title: str = Field(..., description="Title of the action")
    description: str = Field(..., description="Detailed description")
    timeline: str = Field(..., description="Timeline: This week, Next 2 weeks, Ongoing")
    completed: bool = Field(default=False, description="Whether action is completed")


# ── Generate intervention request ────────────────────────────────────────────────

class GenerateInterventionRequest(BaseModel):
    risk_factors: dict = Field(..., description="Student's risk factors from SHAP")
    risk_score: float = Field(..., description="Student's risk score (0-100)")
    risk_level: str = Field(..., description="Risk level: Low, Medium, High, Critical")


# ── Generate intervention response ────────────────────────────────────────────────

class GenerateInterventionResponse(BaseModel):
    id: int
    student_id: int
    priority: str
    summary: str
    actions: list[ActionItem]
    parent_message: str
    status: str
    created_at: datetime


# ── Intervention list response ───────────────────────────────────────────────────

class InterventionListItem(BaseModel):
    id: int
    student_id: int
    priority: str
    summary: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]


class InterventionListResponse(BaseModel):
    interventions: list[InterventionListItem]


# ── Complete intervention request ────────────────────────────────────────────────

class CompleteActionRequest(BaseModel):
    action_index: int = Field(..., description="Index of action to mark complete")


# ── Complete intervention response ───────────────────────────────────────────────

class CompleteActionResponse(BaseModel):
    success: bool
    message: str
