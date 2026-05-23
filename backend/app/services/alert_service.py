"""
backend/app/services/alert_service.py
──────────────────────────────────────
Alert creation, querying, and resolution for the JEE Dropout Prediction System.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.database import Alert, Student, RiskAssessment

log = logging.getLogger(__name__)

# ── Alert type heuristics ─────────────────────────────────────────────────────

def _determine_alert_type(top_factors: list[dict]) -> str:
    """
    Inspect the dominant SHAP factors to classify the alert type.
    Returns one of: 'risk_threshold', 'score_decline', 'burnout_spike'
    """
    if not top_factors:
        return "risk_threshold"

    feature_names = [f.get("feature", "").lower() for f in top_factors[:3]]

    burnout_features = {"burnout_score", "stress_level", "sleep_hours_avg"}
    trend_features   = {"mock_score_trend", "mock_test_avg"}

    if any(f in burnout_features for f in feature_names):
        return "burnout_spike"
    if any(f in trend_features for f in feature_names):
        return "score_decline"
    return "risk_threshold"


def _build_alert_message(
    student: Student,
    risk_level: str,
    risk_score: float,
    top_factors: list[dict],
    batch_name: Optional[str] = None,
) -> str:
    """
    Compose a human-readable alert message from SHAP top factors.
    Example:
      "Student Arjun (B2) has reached HIGH risk (score: 71/100).
       Key factors: Burnout level 8/10, Score declining (-5.2/test),
       Attendance 68%. Immediate counselling recommended."
    """
    LABELS: dict[str, str] = {
        "burnout_score":             "Burnout level {value}/10",
        "stress_level":              "Stress level {value}/10",
        "sleep_hours_avg":           "Sleep only {value} hrs/night",
        "mock_score_trend":          "Score trend {value:+.1f} pts/test",
        "mock_test_avg":             "Mock avg {value:.0f}/360",
        "attendance_rate":           "Attendance {value:.0f}%",
        "assignment_completion_rate":"Assignment completion {value:.0f}%",
        "dpp_accuracy":              "DPP accuracy {value:.0f}%",
        "parental_pressure_level":   "Parental pressure {value}/10",
        "peer_comparison_stress":    "Peer stress {value}/10",
        "study_hours_per_day":       "Studying {value} hrs/day",
        "coaching_engagement_score": "Engagement score {value:.0f}/100",
    }

    batch_tag = f" ({batch_name})" if batch_name else ""
    first_name = student.full_name.split()[0] if student.full_name else "Student"

    # Build factor snippets for top 3 risk-increasing factors
    increasing = [f for f in top_factors if f.get("direction") == "increases_risk"][:3]
    factor_parts: list[str] = []
    for f in increasing:
        tmpl = LABELS.get(f.get("feature", ""))
        if tmpl:
            try:
                factor_parts.append(tmpl.format(value=f.get("actual_value", 0)))
            except (KeyError, ValueError):
                factor_parts.append(f.get("human_label", f["feature"]))
        elif f.get("human_label"):
            factor_parts.append(f["human_label"])

    urgency = {
        "Low":      "Monitor and check in at next session.",
        "Medium":   "Schedule a check-in call within 3 days.",
        "High":     "Immediate faculty intervention recommended.",
        "Critical": "URGENT: Immediate counselling required. Notify parents.",
    }.get(risk_level, "Review student profile.")

    factors_text = (
        "Key factors: " + ", ".join(factor_parts) + "."
        if factor_parts
        else "Please review the full risk report."
    )

    return (
        f"Student {first_name}{batch_tag} has reached {risk_level.upper()} risk "
        f"(score: {risk_score:.0f}/100). "
        f"{factors_text} {urgency}"
    )


# ── Public API ────────────────────────────────────────────────────────────────

def create_alert(
    student_id:    int,
    assessment_id: int,
    risk_level:    str,
    risk_score:    float,
    top_factors:   list[dict],
    db:            Session,
) -> Optional[Alert]:
    """
    Create and persist a new alert for a student's risk assessment.
    Returns the Alert ORM object, or None if creation fails.
    """
    try:
        student: Optional[Student] = db.query(Student).filter_by(id=student_id).first()
        if not student:
            log.warning("create_alert: student_id=%d not found", student_id)
            return None

        # Resolve batch name for the message
        batch_name: Optional[str] = None
        if student.batch:
            batch_name = student.batch.name

        alert_type = _determine_alert_type(top_factors)
        message    = _build_alert_message(student, risk_level, risk_score, top_factors, batch_name)

        alert = Alert(
            student_id    = student_id,
            assessment_id = assessment_id,
            assigned_to   = student.assigned_faculty_id,
            alert_type    = alert_type,
            risk_level    = risk_level,
            message       = message,
            is_resolved   = False,
            is_read       = False,
        )
        db.add(alert)
        db.flush()
        log.info("Alert created: student_id=%d level=%s type=%s", student_id, risk_level, alert_type)
        return alert

    except Exception:
        log.exception("Failed to create alert for student_id=%d", student_id)
        return None


def get_alerts(
    user_id: int,
    role:    str,
    db:      Session,
    skip:    int = 0,
    limit:   int = 50,
    is_resolved: Optional[bool] = None,
    risk_level:  Optional[str]  = None,
) -> list[Alert]:
    """
    Return alerts visible to the requesting user.
      - Admin: all alerts
      - Faculty: only alerts assigned to them
    """
    q = db.query(Alert)

    if role == "faculty":
        q = q.filter(Alert.assigned_to == user_id)

    if is_resolved is not None:
        q = q.filter(Alert.is_resolved == is_resolved)

    if risk_level:
        q = q.filter(Alert.risk_level == risk_level)

    return (
        q.order_by(Alert.created_at.desc())
         .offset(skip)
         .limit(limit)
         .all()
    )


def resolve_alert(
    alert_id: int,
    user_id:  int,
    role:     str,
    note:     Optional[str],
    db:       Session,
) -> Optional[Alert]:
    """Mark an alert as resolved. Faculty may only resolve their own alerts."""
    alert: Optional[Alert] = db.query(Alert).filter_by(id=alert_id).first()
    if not alert:
        return None

    if role == "faculty" and alert.assigned_to != user_id:
        log.warning("Faculty %d tried to resolve alert %d assigned to %d", user_id, alert_id, alert.assigned_to)
        return None

    alert.is_resolved   = True
    alert.resolution_note = note
    db.flush()
    log.info("Alert %d resolved by user %d", alert_id, user_id)
    return alert


def mark_alert_read(alert_id: int, user_id: int, role: str, db: Session) -> Optional[Alert]:
    """Mark a single alert as read."""
    alert: Optional[Alert] = db.query(Alert).filter_by(id=alert_id).first()
    if not alert:
        return None
    if role == "faculty" and alert.assigned_to != user_id:
        return None
    alert.is_read = True
    db.flush()
    return alert


def get_unresolved_count(user_id: int, role: str, db: Session) -> int:
    """Return the number of unresolved alerts visible to the user."""
    q = db.query(Alert).filter(Alert.is_resolved == False)  # noqa: E712
    if role == "faculty":
        q = q.filter(Alert.assigned_to == user_id)
    return q.count()


def get_alert_stats(user_id: int, role: str, db: Session) -> dict:
    """Summary statistics for the alert queue."""
    alerts = get_alerts(user_id, role, db, skip=0, limit=10_000)
    unresolved = [a for a in alerts if not a.is_resolved]

    by_level: dict[str, int] = {}
    for a in unresolved:
        by_level[a.risk_level] = by_level.get(a.risk_level, 0) + 1

    return {
        "total":      len(alerts),
        "unresolved": len(unresolved),
        "by_level":   by_level,
    }
