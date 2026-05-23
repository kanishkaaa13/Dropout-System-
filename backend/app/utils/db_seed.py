"""
backend/app/utils/db_seed.py
─────────────────────────────
Idempotent database seed script for development and demos.

Creates
───────
  1 Institute   — "Demo JEE Institute" (code: DJI)
  3 Batches     — B1 Morning / B2 Evening / B3 Weekend (2025)
  3 Users       — 1 admin + 2 faculty members
  20 Students   — realistic Indian names spread across batches
  10 Mock tests per student  — JEE-realistic scores with trend variation
  8 Surveys per student      — realistic burnout / stress profiles
  60 days of attendance per student (Physics, Chemistry, Maths)
  Risk assessments for all students (uses the actual trained ML models)

Usage
─────
    # From project root:
    python -m backend.app.utils.db_seed

    # Or directly:
    python backend/app/utils/db_seed.py

Environment
───────────
    DATABASE_URL must point to a writable database.
    Defaults to sqlite:///./jee_dropout.db if not set.

Notes
─────
  • The script is IDEMPOTENT: running it multiple times will not create
    duplicate records.  Each entity is looked up by a natural key before
    inserting.
  • ML prediction is run at the end using the models in MODEL_DIR.
    If models are not found, prediction is skipped gracefully.
"""

from __future__ import annotations

import logging
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Make project importable ───────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[4]   # dropout/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import settings
from backend.app.database import SessionLocal, create_all_tables
from backend.app.middleware.auth import hash_password
from backend.app.models.database import (
    Alert,
    AttendanceRecord,
    Batch,
    BlacklistedToken,
    Institute,
    MockTestResult,
    RiskAssessment,
    ShapExplanation,
    Student,
    User,
    WeeklySurvey,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("seed")

rng = random.Random(42)   # deterministic seed


# ─── helpers ──────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _days_ago(n: int) -> datetime:
    return _now() - timedelta(days=n)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


# ─── realistic data pools ─────────────────────────────────────────────────────

INDIAN_NAMES = [
    "Arjun Sharma",    "Priya Verma",     "Rohit Mishra",    "Ananya Singh",
    "Karan Gupta",     "Shreya Patel",    "Vikram Yadav",    "Divya Khanna",
    "Rahul Nair",      "Pooja Agarwal",   "Amit Joshi",      "Neha Dubey",
    "Siddharth Rao",   "Kavya Mehta",     "Aditya Kumar",    "Riya Srivastava",
    "Harshit Tiwari",  "Sakshi Pandey",   "Yash Bhatnagar",  "Tanvi Chauhan",
]

COLLEGES = ["IIT Bombay", "IIT Delhi", "IIT Madras", "IIT Kanpur",
            "IIT Kharagpur", "IIT Roorkee", "IIT Guwahati", "IIT Hyderabad"]

SUBJECTS = ["Physics", "Chemistry", "Maths"]


def _student_profile(idx: int) -> dict:
    """
    Generate a realistic academic + wellbeing profile for one student.
    ~30% of students will have high-risk indicators.
    """
    at_risk = (idx % 10) < 3   # 30% at-risk
    if at_risk:
        base_score     = rng.gauss(110, 30)
        attendance     = rng.gauss(62, 12)
        burnout        = rng.randint(6, 10)
        stress         = rng.randint(6, 10)
        sleep          = rng.gauss(5.0, 0.8)
        study_hrs      = rng.gauss(7.0, 2.0)
        parental       = rng.randint(7, 10)
        motivation     = rng.randint(2, 5)
        trend_slope    = rng.gauss(-15, 10)
    else:
        base_score     = rng.gauss(210, 45)
        attendance     = rng.gauss(82, 8)
        burnout        = rng.randint(2, 6)
        stress         = rng.randint(2, 6)
        sleep          = rng.gauss(6.5, 0.7)
        study_hrs      = rng.gauss(10.0, 1.5)
        parental       = rng.randint(3, 7)
        motivation     = rng.randint(5, 9)
        trend_slope    = rng.gauss(+8, 8)

    return {
        "base_score":    _clamp(base_score, 30, 340),
        "attendance":    _clamp(attendance, 20, 100),
        "burnout":       int(_clamp(burnout, 1, 10)),
        "stress":        int(_clamp(stress, 1, 10)),
        "sleep":         round(_clamp(sleep, 3.0, 9.0), 1),
        "study_hrs":     round(_clamp(study_hrs, 2.0, 14.0), 1),
        "parental":      int(_clamp(parental, 1, 10)),
        "motivation":    int(_clamp(motivation, 1, 10)),
        "trend_slope":   round(trend_slope, 1),
        "at_risk":       at_risk,
    }


def _mock_test_scores(base: float, test_idx: int, slope: float) -> dict:
    """Generate realistic per-subject scores for one test."""
    total = _clamp(base + slope * test_idx + rng.gauss(0, 15), 0, 360)
    # Split total into subjects with natural variation
    p_frac = rng.gauss(0.33, 0.06)
    c_frac = rng.gauss(0.33, 0.06)
    p_frac = _clamp(p_frac, 0.15, 0.50)
    c_frac = _clamp(c_frac, 0.15, 0.50)
    m_frac = max(0, 1.0 - p_frac - c_frac)

    physics   = _clamp(total * p_frac, 0, 120)
    chemistry = _clamp(total * c_frac, 0, 120)
    maths     = _clamp(total * m_frac, 0, 120)
    total     = physics + chemistry + maths

    return {
        "total_score":     round(total, 1),
        "physics_score":   round(physics, 1),
        "chemistry_score": round(chemistry, 1),
        "maths_score":     round(maths, 1),
    }


# ─── seed functions ───────────────────────────────────────────────────────────

def seed_institute(db) -> Institute:
    inst = db.query(Institute).filter_by(code="DJI").first()
    if inst:
        log.info("Institute already exists — skipping.")
        return inst
    inst = Institute(name="Demo JEE Institute", code="DJI", city="Kota")
    db.add(inst)
    db.flush()
    log.info("Created Institute: %s", inst)
    return inst


def seed_batches(db, institute: Institute) -> list[Batch]:
    specs = [
        {"name": "B1 Morning",  "shift": "morning",  "year": 2025, "capacity": 80},
        {"name": "B2 Evening",  "shift": "evening",  "year": 2025, "capacity": 80},
        {"name": "B3 Weekend",  "shift": "weekend",  "year": 2025, "capacity": 40},
    ]
    batches = []
    for s in specs:
        b = db.query(Batch).filter_by(institute_id=institute.id, name=s["name"], year=s["year"]).first()
        if not b:
            b = Batch(
                institute_id=institute.id,
                target_exam="JEE_ADV",
                **s,
            )
            db.add(b)
            db.flush()
            log.info("Created Batch: %s", b)
        batches.append(b)
    return batches


def seed_users(db, institute: Institute) -> tuple[User, User, User]:
    specs = [
        {"email": "admin@demojee.com",    "full_name": "Dr. Pradeep Kumar",    "role": "admin",   "password": "Admin@1234"},
        {"email": "faculty1@demojee.com", "full_name": "Prof. Sunita Sharma",  "role": "faculty", "password": "Faculty@1234"},
        {"email": "faculty2@demojee.com", "full_name": "Prof. Rajesh Agarwal", "role": "faculty", "password": "Faculty@1234"},
    ]
    users = []
    for s in specs:
        u = db.query(User).filter_by(email=s["email"]).first()
        if not u:
            u = User(
                email=s["email"],
                full_name=s["full_name"],
                role=s["role"],
                institute_id=institute.id,
                hashed_password=hash_password(s["password"]),
                is_active=True,
            )
            db.add(u)
            db.flush()
            log.info("Created User: %s", u)
        users.append(u)
    return tuple(users)   # (admin, faculty1, faculty2)


def seed_students(
    db,
    batches: list[Batch],
    faculty_users: tuple[User, User],
) -> list[Student]:
    students = []
    faculty1, faculty2 = faculty_users

    for idx, name in enumerate(INDIAN_NAMES):
        code  = f"JEE2025_{idx+1:03d}"
        email = f"{name.lower().replace(' ', '.')}.{idx+1}@demojee.com"

        s = db.query(Student).filter_by(student_code=code).first()
        if s:
            students.append(s)
            continue

        batch   = batches[idx % len(batches)]
        faculty = faculty1 if idx < 10 else faculty2

        s = Student(
            student_code        = code,
            full_name           = name,
            email               = email,
            batch_id            = batch.id,
            assigned_faculty_id = faculty.id,
            enrollment_date     = _days_ago(180),
            target_rank         = rng.randint(100, 5000),
            target_college      = rng.choice(COLLEGES),
            is_active           = True,
        )
        db.add(s)
        db.flush()
        students.append(s)
        log.info("Created Student: %s", s)

    return students


def seed_mock_tests(db, students: list[Student]) -> None:
    for student in students:
        existing = db.query(MockTestResult).filter_by(student_id=student.id).count()
        if existing >= 10:
            continue

        profile = _student_profile(students.index(student))
        test_types = ["minor", "minor", "major", "minor", "minor",
                      "major", "minor", "minor", "grand_test", "minor"]

        for i in range(10):
            scores    = _mock_test_scores(profile["base_score"], i, profile["trend_slope"])
            test_date = _days_ago(90 - i * 9)
            percentile = _clamp(rng.gauss(50, 20), 1, 99) if not profile["at_risk"] \
                         else _clamp(rng.gauss(25, 15), 1, 60)

            mt = MockTestResult(
                student_id      = student.id,
                test_date       = test_date,
                test_name       = f"Test {i+1}",
                test_type       = test_types[i],
                percentile      = round(percentile, 1),
                rank_in_batch   = rng.randint(1, 80),
                **scores,
            )
            db.add(mt)

    db.flush()
    log.info("Mock tests seeded.")


def seed_surveys(db, students: list[Student]) -> None:
    for student in students:
        existing = db.query(WeeklySurvey).filter_by(student_id=student.id).count()
        if existing >= 8:
            continue

        profile = _student_profile(students.index(student))

        for week_offset in range(8):
            week_date = _days_ago(56 - week_offset * 7)
            iso_week  = week_date.isocalendar()[1]

            # Burnout trends upward for at-risk students over time
            burnout_shift = week_offset * (0.3 if profile["at_risk"] else -0.1)
            burnout = int(_clamp(profile["burnout"] + burnout_shift + rng.randint(-1, 1), 1, 10))

            survey = WeeklySurvey(
                student_id             = student.id,
                week_number            = iso_week,
                survey_date            = week_date,
                burnout_score          = burnout,
                stress_level           = int(_clamp(profile["stress"] + rng.randint(-1, 1), 1, 10)),
                sleep_hours_avg        = round(profile["sleep"] + rng.gauss(0, 0.3), 1),
                study_hours_per_day    = round(profile["study_hrs"] + rng.gauss(0, 0.5), 1),
                parental_pressure      = profile["parental"],
                peer_comparison_stress = int(_clamp(profile["stress"] + rng.randint(-2, 2), 1, 10)),
                motivation_level       = profile["motivation"],
                notes                  = None,
            )
            db.add(survey)

    db.flush()
    log.info("Surveys seeded.")


def seed_attendance(db, students: list[Student]) -> None:
    for student in students:
        existing = db.query(AttendanceRecord).filter_by(student_id=student.id).count()
        if existing >= 60 * len(SUBJECTS):
            continue

        profile = _student_profile(students.index(student))
        attend_rate = profile["attendance"] / 100.0

        for day_offset in range(60):
            att_date = _days_ago(60 - day_offset)
            # Skip Sundays
            if att_date.weekday() == 6:
                continue
            for subject in SUBJECTS:
                present = rng.random() < attend_rate
                # Avoid duplicates
                existing_row = db.query(AttendanceRecord).filter_by(
                    student_id=student.id,
                    date=att_date,
                    subject=subject,
                ).first()
                if not existing_row:
                    db.add(AttendanceRecord(
                        student_id=student.id,
                        date=att_date,
                        subject=subject,
                        present=present,
                    ))

    db.flush()
    log.info("Attendance records seeded.")


def seed_predictions(db, students: list[Student]) -> None:
    """
    Attempt to run ML predictions for all students using the trained models.
    Gracefully skipped if MODEL_DIR doesn't contain the expected .pkl files.
    """
    model_dir = Path(settings.MODEL_DIR)
    if not (model_dir / "metadata.json").exists():
        log.warning("Model files not found at %s — skipping predictions.", model_dir)
        return

    try:
        from backend.app.ml.predictor import JEEDropoutPredictor
        from backend.app.ml.explainer import SHAPExplainer
        from backend.app.ml.risk_scorer import compute_risk_score
        from backend.app.ml.feature_builder import build_features_from_db
    except ImportError as exc:
        log.warning("ML modules import failed (%s) — skipping predictions.", exc)
        return

    predictor = JEEDropoutPredictor(model_dir=str(model_dir))
    predictor.load_models()

    # SHAPExplainer(shap_explainer, preprocessor, feature_cols)
    explainer = SHAPExplainer(
        shap_explainer = predictor.get_shap_explainer(),
        preprocessor   = predictor.get_preprocessor(),
        feature_cols   = predictor.feature_cols,
    )

    for student in students:
        # Skip if already assessed recently
        latest = (
            db.query(RiskAssessment)
            .filter_by(student_id=student.id)
            .order_by(RiskAssessment.assessed_at.desc())
            .first()
        )
        if latest and (datetime.now(timezone.utc) - latest.assessed_at.replace(tzinfo=timezone.utc)).days < 1:
            continue

        try:
            features_df = build_features_from_db(student.id, db)
            if features_df is None:
                continue

            features_dict = features_df.iloc[0].to_dict()
            pred = predictor.predict_single(features_dict)
            risk = compute_risk_score(
                ml_probability    = pred["ensemble_probability"],
                burnout_score     = features_dict["burnout_score"],
                mock_score_trend  = features_dict["mock_score_trend"],
                attendance_rate   = features_dict["attendance_rate"],
                sleep_hours       = features_dict["sleep_hours_avg"],
                parental_pressure = features_dict["parental_pressure_level"],
            )
            explanation  = explainer.explain(features_df)
            summary_text = explainer.generate_summary_text(
                explanation["top_factors"],
                student_name=student.full_name.split()[0],
            )

            assessment = RiskAssessment(
                student_id       = student.id,
                assessed_at      = _now(),
                risk_score       = risk["score"],
                risk_level       = risk["level"],
                ml_probability   = pred["ensemble_probability"],
                model_version    = pred["model_version"],
                feature_snapshot = features_dict,
            )
            db.add(assessment)
            db.flush()

            db.add(ShapExplanation(
                assessment_id = assessment.id,
                base_value    = explanation["base_value"],
                top_factors   = explanation["top_factors"],
                summary_text  = summary_text,
            ))

            if risk["level"] in ("Medium", "High", "Critical"):
                db.add(Alert(
                    student_id    = student.id,
                    assessment_id = assessment.id,
                    assigned_to   = student.assigned_faculty_id,
                    alert_type    = "risk_threshold",
                    risk_level    = risk["level"],
                    message       = (
                        f"Student '{student.full_name}' flagged as "
                        f"{risk['level']} risk (score={risk['score']:.1f}/100). "
                        f"{summary_text}"
                    ),
                ))

            log.info("Predicted: %-22s → %s (%.1f)", student.full_name, risk["level"], risk["score"])

        except Exception as exc:
            log.warning("Prediction failed for student_id=%d: %s", student.id, exc)

    db.flush()
    log.info("Predictions complete.")


# ─── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    log.info("=" * 60)
    log.info("JEE Dropout Prediction System — Database Seed")
    log.info("Database: %s", settings.DATABASE_URL[:60])
    log.info("=" * 60)

    # Ensure all tables exist
    create_all_tables()

    db = SessionLocal()
    try:
        # 1. Institute
        institute = seed_institute(db)

        # 2. Batches
        batches = seed_batches(db, institute)

        # 3. Users
        admin, faculty1, faculty2 = seed_users(db, institute)

        # 4. Students
        students = seed_students(db, batches, (faculty1, faculty2))

        # 5. Mock tests
        seed_mock_tests(db, students)

        # 6. Surveys
        seed_surveys(db, students)

        # 7. Attendance
        seed_attendance(db, students)

        db.commit()
        log.info("Core seed data committed.")

        # 8. ML Predictions (separate commit per student)
        seed_predictions(db, students)
        db.commit()
        log.info("Predictions committed.")

        log.info("=" * 60)
        log.info("Seed complete!")
        log.info("  Institute : 1")
        log.info("  Batches   : %d", len(batches))
        log.info("  Users     : 3 (1 admin + 2 faculty)")
        log.info("  Students  : %d", len(students))
        log.info("")
        log.info("Login credentials:")
        log.info("  admin@demojee.com    / Admin@1234")
        log.info("  faculty1@demojee.com / Faculty@1234")
        log.info("  faculty2@demojee.com / Faculty@1234")
        log.info("=" * 60)

    except Exception as exc:
        db.rollback()
        log.exception("Seed failed: %s", exc)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
