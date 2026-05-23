"""
feature_builder.py
──────────────────
JEE Dropout Prediction System — Dual-pipeline feature builder.

Supports two prediction pipelines:
  1. SYNTHETIC (default) — 17 numeric features derived from mock tests,
     weekly surveys, and attendance records. Used when student profile
     fields (jee_main_score etc.) are absent.
  2. REAL — 14 features (6 numeric + 8 categorical) pulled directly from
     the Student profile fields added in the v2 schema. Used when
     jee_main_score is present on the student record.

The main entry point ``build_features_from_db`` auto-detects which
pipeline to use based on whether real-dataset profile fields are set.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import numpy as np
import pandas as pd
from scipy.stats import linregress

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE 1: Synthetic — 17 numeric features
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULTS_SYNTHETIC: dict[str, float] = {
    "attendance_rate":             80.0,
    "mock_test_avg":               200.0,
    "physics_score":               66.0,
    "chemistry_score":             66.0,
    "maths_score":                 66.0,
    "mock_score_trend":            0.0,
    "assignment_completion_rate":  70.0,
    "dpp_accuracy":                60.0,
    "test_attempt_rate":           75.0,
    "burnout_score":               4.0,
    "stress_level":                4.0,
    "sleep_hours_avg":             6.5,
    "study_hours_per_day":         6.0,
    "study_consistency_score":     60.0,
    "parental_pressure_level":     5.0,
    "peer_comparison_stress":      5.0,
    "coaching_engagement_score":   60.0,
}

FEATURE_COLS: list[str] = list(_DEFAULTS_SYNTHETIC.keys())


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE 2: Real dataset — 14 features (6 numeric + 8 categorical)
# ─────────────────────────────────────────────────────────────────────────────

REAL_NUMERIC_FEATURES: list[str] = [
    "jee_main_score",
    "jee_advanced_score",
    "mock_test_score_avg",
    "class_12_percent",
    "attempt_count",
    "daily_study_hours",
]

REAL_CATEGORICAL_FEATURES: list[str] = [
    "school_board",
    "coaching_institute",
    "family_income",
    "parent_education",
    "location_type",
    "peer_pressure_level",
    "mental_health_issues",
    "admission_taken",
]

REAL_FEATURE_COLS: list[str] = REAL_NUMERIC_FEATURES + REAL_CATEGORICAL_FEATURES

_DEFAULTS_REAL: dict[str, Any] = {
    "jee_main_score":       60.0,
    "jee_advanced_score":   40.0,
    "mock_test_score_avg":  55.0,
    "class_12_percent":     70.0,
    "attempt_count":        1,
    "daily_study_hours":    6.0,
    "school_board":         "CBSE",
    "coaching_institute":   "Local",
    "family_income":        "Mid",
    "parent_education":     "Graduate",
    "location_type":        "Urban",
    "peer_pressure_level":  "Medium",
    "mental_health_issues": "No",
    "admission_taken":      "No",
}


# ─────────────────────────────────────────────────────────────────────────────
# Pure math helpers (shared)
# ─────────────────────────────────────────────────────────────────────────────

def compute_mock_score_trend(scores: list[float]) -> float:
    """Linear regression slope of mock test scores. Returns 0.0 if < 2 points."""
    if len(scores) < 2:
        return 0.0
    recent = scores[-5:]
    x = list(range(len(recent)))
    slope, _, _, _, _ = linregress(x, recent)
    return float(np.clip(slope, -100.0, 100.0))


def compute_study_consistency(daily_hours: list[float]) -> float:
    """0–100 study consistency score. Higher std → lower score."""
    if not daily_hours or len(daily_hours) < 2:
        return _DEFAULTS_SYNTHETIC["study_consistency_score"]
    std = float(np.std(daily_hours, ddof=0))
    return float(np.clip(100.0 - std * 10.0, 0.0, 100.0))


def compute_coaching_engagement(
    attendance_rate: float,
    stress_level: float,
    burnout_score: float,
) -> float:
    """Composite coaching engagement score (0–100)."""
    raw = (
        attendance_rate * 0.40
        + (10 - stress_level) * 3.0
        + (10 - burnout_score) * 2.5
        + 15.0
    )
    return float(np.clip(raw, 0.0, 100.0))


# ─────────────────────────────────────────────────────────────────────────────
# Synthetic pipeline DB helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_mock_test_features(
    student_id: int,
    db: Any,
    lookback_tests: int = 5,
) -> dict[str, float | None]:
    try:
        from backend.app.models.database import MockTestResult
        rows = (
            db.query(MockTestResult)
            .filter(MockTestResult.student_id == student_id)
            .order_by(MockTestResult.test_date.desc())
            .limit(lookback_tests)
            .all()
        )
        if not rows:
            return {k: None for k in ["mock_test_avg", "physics_score",
                    "chemistry_score", "maths_score", "mock_score_trend",
                    "test_attempt_rate"]}
        rows = list(reversed(rows))
        totals    = [r.total_score   for r in rows if r.total_score   is not None]
        physics   = [r.physics_score for r in rows if r.physics_score is not None]
        chemistry = [r.chemistry_score for r in rows if r.chemistry_score is not None]
        maths     = [r.maths_score   for r in rows if r.maths_score   is not None]
        return {
            "mock_test_avg":    float(np.mean(totals))    if totals    else None,
            "physics_score":    float(np.mean(physics))   if physics   else None,
            "chemistry_score":  float(np.mean(chemistry)) if chemistry else None,
            "maths_score":      float(np.mean(maths))     if maths     else None,
            "mock_score_trend": compute_mock_score_trend(totals),
            "test_attempt_rate": None,
        }
    except Exception as exc:
        logger.error("Mock test query failed for student_id=%d: %s", student_id, exc)
        return {k: None for k in ["mock_test_avg", "physics_score", "chemistry_score",
                                   "maths_score", "mock_score_trend", "test_attempt_rate"]}


def _get_survey_features(
    student_id: int,
    db: Any,
    lookback_weeks: int = 2,
) -> dict[str, float | None]:
    try:
        from backend.app.models.database import WeeklySurvey
        cutoff = datetime.utcnow() - timedelta(weeks=lookback_weeks)
        rows = (
            db.query(WeeklySurvey)
            .filter(WeeklySurvey.student_id == student_id,
                    WeeklySurvey.survey_date >= cutoff)
            .order_by(WeeklySurvey.survey_date.desc())
            .all()
        )
        if not rows:
            return {k: None for k in ["burnout_score", "stress_level",
                    "sleep_hours_avg", "study_hours_per_day",
                    "parental_pressure_level", "peer_comparison_stress"]}

        def _avg(field: str) -> float | None:
            vals = [getattr(r, field) for r in rows if getattr(r, field) is not None]
            return float(np.mean(vals)) if vals else None

        return {
            "burnout_score":           _avg("burnout_score"),
            "stress_level":            _avg("stress_level"),
            "sleep_hours_avg":         _avg("sleep_hours_avg"),
            "study_hours_per_day":     _avg("study_hours_per_day"),
            "parental_pressure_level": _avg("parental_pressure"),
            "peer_comparison_stress":  _avg("peer_comparison_stress"),
        }
    except Exception as exc:
        logger.error("Survey query failed for student_id=%d: %s", student_id, exc)
        return {k: None for k in ["burnout_score", "stress_level", "sleep_hours_avg",
                                   "study_hours_per_day", "parental_pressure_level",
                                   "peer_comparison_stress"]}


def _get_attendance_features(
    student_id: int,
    db: Any,
    lookback_days: int = 30,
) -> dict[str, float | None]:
    try:
        from backend.app.models.database import AttendanceRecord
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)
        rows = (
            db.query(AttendanceRecord)
            .filter(AttendanceRecord.student_id == student_id,
                    AttendanceRecord.date >= cutoff)
            .all()
        )
        if not rows:
            return {"attendance_rate": None}
        rate = float(sum(1 for r in rows if r.present) / len(rows) * 100)
        return {"attendance_rate": round(rate, 2)}
    except Exception as exc:
        logger.error("Attendance query failed for student_id=%d: %s", student_id, exc)
        return {"attendance_rate": None}


def _get_assignment_features(student_id: int, db: Any) -> dict[str, float | None]:
    return {"assignment_completion_rate": None, "dpp_accuracy": None}


# ─────────────────────────────────────────────────────────────────────────────
# Real-dataset pipeline builder
# ─────────────────────────────────────────────────────────────────────────────

def build_real_features_from_student(
    student: Any,
    db: Any,
) -> pd.DataFrame:
    """
    Build the 14-feature real-dataset vector from the Student ORM object.

    6 numeric features come directly from the student profile.
    mock_test_score_avg and daily_study_hours are derived from mock tests
    and surveys respectively if available, otherwise defaults are used.
    8 categorical features come from student profile string fields.
    """
    student_id = student.id

    # ── Numeric: from profile ─────────────────────────────────────────────────
    feats: dict[str, Any] = {
        "jee_main_score":     student.jee_main_score     or _DEFAULTS_REAL["jee_main_score"],
        "jee_advanced_score": student.jee_advanced_score or _DEFAULTS_REAL["jee_advanced_score"],
        "class_12_percent":   _DEFAULTS_REAL["class_12_percent"],   # not in current schema
        "attempt_count":      student.attempt_count      or _DEFAULTS_REAL["attempt_count"],
        "daily_study_hours":  _DEFAULTS_REAL["daily_study_hours"],
        "mock_test_score_avg": _DEFAULTS_REAL["mock_test_score_avg"],
    }

    # Override mock_test_score_avg from DB if records exist
    try:
        from backend.app.models.database import MockTestResult, WeeklySurvey
        mock_rows = (
            db.query(MockTestResult)
            .filter(MockTestResult.student_id == student_id)
            .order_by(MockTestResult.test_date.desc())
            .limit(5).all()
        )
        if mock_rows:
            totals = [r.total_score for r in mock_rows if r.total_score is not None]
            if totals:
                # Convert 0-360 JEE scale to 0-100 percentile approximation
                feats["mock_test_score_avg"] = float(np.mean(totals)) / 3.6

        # daily_study_hours from most recent survey
        survey = (
            db.query(WeeklySurvey)
            .filter(WeeklySurvey.student_id == student_id)
            .order_by(WeeklySurvey.survey_date.desc())
            .first()
        )
        if survey and getattr(survey, "study_hours_per_day", None):
            feats["daily_study_hours"] = float(survey.study_hours_per_day)
    except Exception as exc:
        logger.warning("Could not enrich real features from DB for student_id=%d: %s",
                       student_id, exc)

    # ── Categorical: from profile ─────────────────────────────────────────────
    feats["school_board"]         = student.school_board         or _DEFAULTS_REAL["school_board"]
    feats["coaching_institute"]   = student.coaching_institute_name or _DEFAULTS_REAL["coaching_institute"]
    feats["family_income"]        = student.family_income        or _DEFAULTS_REAL["family_income"]
    feats["parent_education"]     = student.parent_education     or _DEFAULTS_REAL["parent_education"]
    feats["location_type"]        = student.location_type        or _DEFAULTS_REAL["location_type"]
    feats["peer_pressure_level"]  = student.peer_pressure_level  or _DEFAULTS_REAL["peer_pressure_level"]
    feats["mental_health_issues"] = student.mental_health_issues or _DEFAULTS_REAL["mental_health_issues"]
    feats["admission_taken"]      = student.admission_taken      or _DEFAULTS_REAL["admission_taken"]

    df = pd.DataFrame([feats], columns=REAL_FEATURE_COLS)
    df.index = [student_id]
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point — auto-detects pipeline
# ─────────────────────────────────────────────────────────────────────────────

def build_features_from_db(
    student_id: int,
    db_session: Any,
) -> Optional[pd.DataFrame]:
    """
    Auto-detect which pipeline to use and return a feature DataFrame.

    - If the student has jee_main_score set → real-dataset pipeline (14 features)
    - Otherwise → synthetic pipeline (17 numeric features)

    Returns None if the student does not exist.
    """
    try:
        from backend.app.models.database import Student
        student = db_session.query(Student).filter(Student.id == student_id).first()
        if student is None:
            logger.error("Student id=%d not found in DB.", student_id)
            return None
    except Exception as exc:
        logger.error("Student lookup failed for id=%d: %s", student_id, exc)
        return None

    # Auto-detect: use real pipeline if JEE score fields are populated
    if getattr(student, "jee_main_score", None) is not None:
        logger.info("student_id=%d → using REAL dataset pipeline (14 features)", student_id)
        return build_real_features_from_student(student, db_session)

    # Fallback: synthetic pipeline
    logger.info("student_id=%d → using SYNTHETIC pipeline (17 features)", student_id)
    mock_feats       = _get_mock_test_features(student_id, db_session)
    survey_feats     = _get_survey_features(student_id, db_session)
    attendance_feats = _get_attendance_features(student_id, db_session)
    assignment_feats = _get_assignment_features(student_id, db_session)

    merged: dict[str, float | None] = {
        **mock_feats, **survey_feats, **attendance_feats, **assignment_feats,
    }
    merged.setdefault("study_consistency_score", None)

    if all(merged.get(k) is not None for k in
           ("attendance_rate", "stress_level", "burnout_score")):
        merged["coaching_engagement_score"] = compute_coaching_engagement(
            float(merged["attendance_rate"]),   # type: ignore[arg-type]
            float(merged["stress_level"]),       # type: ignore[arg-type]
            float(merged["burnout_score"]),      # type: ignore[arg-type]
        )
    else:
        merged.setdefault("coaching_engagement_score", None)

    features: dict[str, float] = {}
    for col in FEATURE_COLS:
        val = merged.get(col)
        features[col] = float(val) if val is not None else float(_DEFAULTS_SYNTHETIC[col])

    df = pd.DataFrame([features], columns=FEATURE_COLS)
    df.index = [student_id]
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Convenience: build from dict (tests / predict form)
# ─────────────────────────────────────────────────────────────────────────────

def build_features_from_dict(
    raw: dict[str, Any],
    fill_missing_with_defaults: bool = True,
    pipeline: str = "synthetic",
) -> pd.DataFrame:
    """
    Build a feature DataFrame from a plain dict.

    Parameters
    ----------
    raw      : dict of feature values
    pipeline : "synthetic" (17 numeric) or "real" (14 mixed)
    """
    if pipeline == "real":
        cols = REAL_FEATURE_COLS
        defaults = _DEFAULTS_REAL
    else:
        cols = FEATURE_COLS
        defaults = _DEFAULTS_SYNTHETIC  # type: ignore[assignment]

    features: dict[str, Any] = {}
    for col in cols:
        if col in raw and raw[col] is not None:
            features[col] = raw[col]
        elif fill_missing_with_defaults:
            features[col] = defaults[col]
        else:
            raise ValueError(f"Missing required feature: '{col}'")

    return pd.DataFrame([features], columns=cols)
