"""
backend/app/services/scheduler.py
──────────────────────────────────
APScheduler background jobs for the JEE Dropout Prediction System.

Jobs
────
  weekly_risk_reassessment  — Every Sunday at 2 AM IST
  daily_alert_digest        — Every morning at 7 AM IST

Registration
────────────
  Call start_scheduler(app) from the FastAPI lifespan startup.
  Call stop_scheduler() from lifespan shutdown.
"""

from __future__ import annotations

import logging
from datetime import timezone, timedelta
from typing   import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron      import CronTrigger

log = logging.getLogger(__name__)

# IST = UTC+5:30
IST_OFFSET  = timedelta(hours=5, minutes=30)
_scheduler: Optional[AsyncIOScheduler] = None


# ── Job implementations ───────────────────────────────────────────────────────

async def weekly_risk_reassessment() -> None:
    """
    Re-run ML predictions for all active students.
    Creates new Alerts if risk level has changed or crossed threshold.
    Runs every Sunday at 2 AM IST (20:30 UTC Saturday).
    """
    log.info("[Scheduler] weekly_risk_reassessment — starting")
    try:
        from backend.app.database                   import SessionLocal
        from backend.app.models.database            import Student, RiskAssessment, Alert
        from backend.app.ml.predictor               import JEEDropoutPredictor
        from backend.app.ml.explainer               import SHAPExplainer
        from backend.app.ml.risk_scorer             import compute_risk_score
        from backend.app.ml.feature_builder         import build_features_from_db
        from backend.app.services.alert_service     import create_alert
        from backend.app.config                     import settings
        from pathlib                                import Path
        from datetime                               import datetime

        model_dir = Path(settings.MODEL_DIR)
        if not (model_dir / "metadata.json").exists():
            log.warning("[Scheduler] Model files not found at %s — skipping", model_dir)
            return

        predictor = JEEDropoutPredictor(model_dir=str(model_dir))
        predictor.load_models()
        explainer = SHAPExplainer(
            shap_explainer=predictor.get_shap_explainer(),
            preprocessor=predictor.get_preprocessor(),
            feature_cols=predictor.feature_cols,
        )

        db = SessionLocal()
        assessed = 0
        alerted  = 0
        try:
            students = db.query(Student).filter_by(is_active=True).all()
            log.info("[Scheduler] Re-assessing %d active students", len(students))

            for student in students:
                try:
                    features_df = build_features_from_db(student.id, db)
                    if features_df is None:
                        continue

                    features_dict = features_df.iloc[0].to_dict()
                    pred          = predictor.predict_single(features_dict)
                    risk          = compute_risk_score(
                        ml_probability    = pred["ensemble_probability"],
                        burnout_score     = features_dict.get("burnout_score", 5),
                        mock_score_trend  = features_dict.get("mock_score_trend", 0),
                        attendance_rate   = features_dict.get("attendance_rate", 75),
                        sleep_hours       = features_dict.get("sleep_hours_avg", 6),
                        parental_pressure = features_dict.get("parental_pressure_level", 5),
                    )
                    explanation = explainer.explain(features_df)

                    # Get previous risk level for comparison
                    prev = (
                        db.query(RiskAssessment)
                        .filter_by(student_id=student.id)
                        .order_by(RiskAssessment.assessed_at.desc())
                        .first()
                    )
                    prev_level = prev.risk_level if prev else None

                    assessment = RiskAssessment(
                        student_id       = student.id,
                        assessed_at      = datetime.now(timezone.utc),
                        risk_score       = risk["score"],
                        risk_level       = risk["level"],
                        ml_probability   = pred["ensemble_probability"],
                        model_version    = pred.get("model_version", "1.0"),
                        feature_snapshot = features_dict,
                    )
                    db.add(assessment)
                    db.flush()
                    assessed += 1

                    # Alert if: High/Critical, or risk level worsened
                    ALERT_LEVELS = {"High", "Critical"}
                    level_order  = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
                    current_ord  = level_order.get(risk["level"], 0)
                    prev_ord     = level_order.get(prev_level, 0)

                    if risk["level"] in ALERT_LEVELS or current_ord > prev_ord:
                        alert = create_alert(
                            student_id    = student.id,
                            assessment_id = assessment.id,
                            risk_level    = risk["level"],
                            risk_score    = risk["score"],
                            top_factors   = explanation.get("top_factors", []),
                            db            = db,
                        )
                        if alert:
                            alerted += 1

                except Exception as exc:
                    log.warning("[Scheduler] student_id=%d failed: %s", student.id, exc)

            db.commit()
            log.info("[Scheduler] weekly_risk_reassessment done — assessed=%d alerted=%d", assessed, alerted)

        except Exception as exc:
            db.rollback()
            log.exception("[Scheduler] weekly_risk_reassessment DB error: %s", exc)
        finally:
            db.close()

    except ImportError as exc:
        log.error("[Scheduler] Import error in weekly_risk_reassessment: %s", exc)


async def daily_alert_digest() -> None:
    """
    Send a morning digest email to each faculty member listing their
    students who have unresolved alerts.
    Runs every day at 7 AM IST (01:30 UTC).
    """
    log.info("[Scheduler] daily_alert_digest — starting")
    try:
        from backend.app.database               import SessionLocal
        from backend.app.models.database        import Alert, Student, User
        from backend.app.services.email_service import send_daily_digest
        from sqlalchemy                         import func

        db = SessionLocal()
        sent = 0
        try:
            # All faculty members
            faculty_users = db.query(User).filter(
                User.role == "faculty",
                User.is_active == True,          # noqa: E712
            ).all()

            for faculty in faculty_users:
                # Find unresolved alerts assigned to this faculty
                unresolved = (
                    db.query(Alert)
                    .filter(
                        Alert.assigned_to  == faculty.id,
                        Alert.is_resolved  == False,         # noqa: E712
                    )
                    .all()
                )

                if not unresolved:
                    continue   # nothing to report

                # Build per-student summary
                student_map: dict[int, dict] = {}
                for alert in unresolved:
                    sid = alert.student_id
                    if sid not in student_map:
                        stu = db.query(Student).filter_by(id=sid).first()
                        student_map[sid] = {
                            "student_name": stu.full_name if stu else f"Student {sid}",
                            "risk_level":   alert.risk_level,
                            "alert_count":  0,
                        }
                    student_map[sid]["alert_count"] += 1
                    # Escalate to worst risk level seen
                    ORDER = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
                    if ORDER.get(alert.risk_level, 0) > ORDER.get(student_map[sid]["risk_level"], 0):
                        student_map[sid]["risk_level"] = alert.risk_level

                items = sorted(
                    student_map.values(),
                    key=lambda x: {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}.get(x["risk_level"], 0),
                    reverse=True,
                )

                ok = send_daily_digest(
                    faculty_email = faculty.email,
                    faculty_name  = faculty.full_name or faculty.email,
                    items         = items,
                )
                if ok:
                    sent += 1

            log.info("[Scheduler] daily_alert_digest done — digests_sent=%d", sent)

        except Exception as exc:
            log.exception("[Scheduler] daily_alert_digest error: %s", exc)
        finally:
            db.close()

    except ImportError as exc:
        log.error("[Scheduler] Import error in daily_alert_digest: %s", exc)


# ── Scheduler lifecycle ───────────────────────────────────────────────────────

def start_scheduler() -> AsyncIOScheduler:
    """
    Configure and start the APScheduler AsyncIOScheduler.
    Returns the scheduler instance for later shutdown.
    """
    global _scheduler

    _scheduler = AsyncIOScheduler(timezone="UTC")

    # Weekly reassessment: Sunday 2 AM IST = Saturday 20:30 UTC
    _scheduler.add_job(
        weekly_risk_reassessment,
        trigger=CronTrigger(day_of_week="sat", hour=20, minute=30, timezone="UTC"),
        id="weekly_risk_reassessment",
        name="Weekly student risk re-assessment",
        replace_existing=True,
        misfire_grace_time=3600,   # 1 hour grace if server was down
    )

    # Daily digest: 7 AM IST = 01:30 UTC
    _scheduler.add_job(
        daily_alert_digest,
        trigger=CronTrigger(hour=1, minute=30, timezone="UTC"),
        id="daily_alert_digest",
        name="Daily faculty alert digest emails",
        replace_existing=True,
        misfire_grace_time=1800,
    )

    _scheduler.start()
    log.info(
        "[Scheduler] Started — jobs: %s",
        [j.id for j in _scheduler.get_jobs()],
    )
    return _scheduler


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler on application exit."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("[Scheduler] Stopped.")
    _scheduler = None


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """Return the running scheduler instance (or None)."""
    return _scheduler
