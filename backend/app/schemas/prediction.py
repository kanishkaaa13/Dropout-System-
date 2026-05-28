"""
schemas/prediction.py
─────────────────────
Pydantic schemas for prediction and SHAP explanation endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Feature input (manual prediction via API) ─────────────────────────────────

class StudentFeaturesInput(BaseModel):
    """All 17 JEE features for a manual single-student prediction."""

    attendance_rate:            float = Field(..., ge=0, le=100)
    mock_test_avg:              float = Field(..., ge=0, le=360)
    physics_score:              float = Field(..., ge=0, le=120)
    chemistry_score:            float = Field(..., ge=0, le=120)
    maths_score:                float = Field(..., ge=0, le=120)
    mock_score_trend:           float = Field(..., ge=-100, le=100)
    assignment_completion_rate: float = Field(..., ge=0, le=100)
    dpp_accuracy:               float = Field(..., ge=0, le=100)
    test_attempt_rate:          float = Field(..., ge=0, le=100)
    burnout_score:              int   = Field(..., ge=1, le=10)
    stress_level:               int   = Field(..., ge=1, le=10)
    sleep_hours_avg:            float = Field(..., ge=3, le=12)
    study_hours_per_day:        float = Field(..., ge=0, le=16)
    study_consistency_score:    float = Field(..., ge=0, le=100)
    parental_pressure_level:    int   = Field(..., ge=1, le=10)
    peer_comparison_stress:     int   = Field(..., ge=1, le=10)
    coaching_engagement_score:  float = Field(..., ge=0, le=100)


# ── SHAP impact item ──────────────────────────────────────────────────────────

class FeatureImpact(BaseModel):
    feature:      str
    human_label:  str
    shap_value:   float
    actual_value: float
    direction:    str    # "increases_risk" | "decreases_risk"
    magnitude:    float
    unit:         str
    severity:     str


# ── Risk score components ──────────────────────────────────────────────────────

class RiskComponents(BaseModel):
    ml_base:                float
    burnout_contribution:   float
    trend_contribution:     float
    sleep_contribution:     float
    pressure_contribution:  float
    attendance_contribution: float
    total_bonus:            float


# ── Main prediction response ──────────────────────────────────────────────────

class PredictionResponse(BaseModel):
    student_id:          int
    assessment_id:       int
    risk_score:          float
    risk_level:          str
    risk_color:          str
    urgency:             str
    ml_probability:      float
    predicted_dropout:   bool
    risk_components:     RiskComponents
    top_risk_factors:    list[FeatureImpact]
    counselor_summary:   str
    model_version:       str
    assessed_at:         datetime
    alert_created:       bool
    inference_time_ms:   float


# ── Explanation-only response ─────────────────────────────────────────────────

class ExplanationResponse(BaseModel):
    student_id:       int
    assessment_id:    int
    assessed_at:      datetime
    base_value:       float
    top_factors:      list[FeatureImpact]
    counselor_summary: Optional[str]
    risk_score:       Optional[float]
    risk_level:       Optional[str]


# ── Waterfall plot response ───────────────────────────────────────────────────

class WaterfallPlotResponse(BaseModel):
    student_id:    int
    assessment_id: int
    plot_base64:   str      # base64-encoded PNG
    assessed_at:   datetime


# ── Simplified explanation response for frontend ──────────────────────────────

class SimpleFactor(BaseModel):
    feature: str
    impact: float
    value: str
    direction: str  # "risk" | "protective"


class SimpleExplanationResponse(BaseModel):
    risk_score: float
    factors: list[SimpleFactor]
