"""
models/database.py
──────────────────
Complete SQLAlchemy ORM model layer for the JEE Dropout Prediction System.

Models
------
  Institute         — coaching institute (Allen, Aakash, FIITJEE …)
  Batch             — course batch within an institute
  User              — admin / faculty accounts
  Student           — JEE aspirant enrolled in a batch
  MockTestResult    — individual test score record
  WeeklySurvey      — self-reported wellbeing survey (burnout, stress …)
  AttendanceRecord  — per-day, per-subject attendance mark
  RiskAssessment    — ML prediction output persisted to DB
  ShapExplanation   — SHAP feature-impact data linked to an assessment
  Alert             — counsellor notification generated from high-risk assessment
  AuditLog          — immutable record of every state-changing API action
  BlacklistedToken  — invalidated JWT refresh tokens (logout mechanism)

Design notes
------------
  • All timestamps use server_default=text("NOW()") so the DB controls
    the clock even when the ORM object is created without an explicit value.
  • JSON columns (feature_snapshot, top_factors, details) are stored as
    native jsonb on PostgreSQL and as text-serialised JSON on SQLite.
  • Composite indexes are defined where multi-column queries are common
    (e.g., student_id + assessed_at for trend charts).
  • __repr__ methods are concise and safe (no lazy-loaded relationships).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


# ─── Institute ────────────────────────────────────────────────────────────────

class Institute(Base):
    """Coaching institute entity (e.g., Allen Kota — JK Campus)."""

    __tablename__ = "institutes"

    id:         Mapped[int]       = mapped_column(Integer, primary_key=True, index=True)
    name:       Mapped[str]       = mapped_column(String(200), nullable=False)
    code:       Mapped[str]       = mapped_column(String(20), unique=True, nullable=False, index=True)
    city:       Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime]  = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    # Relationships
    batches: Mapped[list[Batch]] = relationship("Batch", back_populates="institute", lazy="select")
    users:   Mapped[list[User]]  = relationship("User",  back_populates="institute", lazy="select")

    def __repr__(self) -> str:
        return f"<Institute id={self.id} code={self.code!r} name={self.name!r}>"


# ─── Batch ────────────────────────────────────────────────────────────────────

class Batch(Base):
    """Course batch within an institute (e.g., B1 Morning 2025 JEE)."""

    __tablename__ = "batches"

    id:           Mapped[int]       = mapped_column(Integer, primary_key=True, index=True)
    institute_id: Mapped[int]       = mapped_column(ForeignKey("institutes.id", ondelete="RESTRICT"), nullable=False, index=True)
    name:         Mapped[str]       = mapped_column(String(100), nullable=False)
    year:         Mapped[int | None] = mapped_column(Integer)
    shift:        Mapped[str | None] = mapped_column(String(20))      # morning / evening / weekend
    target_exam:  Mapped[str | None] = mapped_column(String(20))      # JEE_MAIN / JEE_ADV / NEET
    capacity:     Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("institute_id", "name", "year", name="uq_batch_institute_name_year"),
        Index("ix_batches_institute_year", "institute_id", "year"),
    )

    # Relationships
    institute: Mapped[Institute]     = relationship("Institute", back_populates="batches")
    students:  Mapped[list[Student]] = relationship("Student",   back_populates="batch", lazy="select")

    def __repr__(self) -> str:
        return f"<Batch id={self.id} name={self.name!r} year={self.year}>"


# ─── User ─────────────────────────────────────────────────────────────────────

class User(Base):
    """
    Admin or faculty account.

    Roles
    -----
    admin   — full access to all institutes / batches
    faculty — access limited to their assigned students
    """

    __tablename__ = "users"

    id:              Mapped[int]            = mapped_column(Integer, primary_key=True, index=True)
    email:           Mapped[str]            = mapped_column(String(200), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str]            = mapped_column(String(200), nullable=False)
    full_name:       Mapped[str | None]     = mapped_column(String(200))
    role:            Mapped[str]            = mapped_column(String(20), nullable=False, default="faculty", index=True)
    institute_id:    Mapped[int | None]     = mapped_column(ForeignKey("institutes.id", ondelete="SET NULL"))
    is_active:       Mapped[bool]           = mapped_column(Boolean, nullable=False, default=True)
    created_at:      Mapped[datetime]       = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    last_login:      Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    institute:        Mapped[Institute | None]    = relationship("Institute", back_populates="users")
    assigned_students: Mapped[list[Student]]      = relationship(
        "Student", foreign_keys="[Student.assigned_faculty_id]", back_populates="assigned_faculty", lazy="select"
    )
    audit_logs:       Mapped[list[AuditLog]]      = relationship("AuditLog", back_populates="user", lazy="select")
    assigned_alerts:  Mapped[list[Alert]]         = relationship(
        "Alert", foreign_keys="[Alert.assigned_to]", back_populates="assignee", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"


# ─── Student ──────────────────────────────────────────────────────────────────

class Student(Base):
    """JEE aspirant enrolled in a coaching batch."""

    __tablename__ = "students"

    id:                  Mapped[int]            = mapped_column(Integer, primary_key=True, index=True)
    student_code:        Mapped[str | None]     = mapped_column(String(30), unique=True, index=True)
    full_name:           Mapped[str]            = mapped_column(String(200), nullable=False)
    email:               Mapped[str | None]     = mapped_column(String(200), unique=True, index=True)
    phone:               Mapped[str | None]     = mapped_column(String(20))
    batch_id:            Mapped[int | None]     = mapped_column(ForeignKey("batches.id", ondelete="SET NULL"), index=True)
    assigned_faculty_id: Mapped[int | None]     = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    enrollment_date:     Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    target_rank:         Mapped[int | None]     = mapped_column(Integer)
    target_college:      Mapped[str | None]     = mapped_column(String(200))
    is_active:           Mapped[bool]           = mapped_column(Boolean, nullable=False, default=True)
    is_demo:             Mapped[bool]           = mapped_column(Boolean, nullable=False, default=False, index=True)

    # ── Real-dataset profile fields (JEE Dropout After Class 12) ─────────────
    jee_main_score:          Mapped[float | None]  = mapped_column(Float)              # 0–100 percentile
    jee_advanced_score:      Mapped[float | None]  = mapped_column(Float)              # 0–100 percentile
    school_board:            Mapped[str | None]    = mapped_column(String(20))         # CBSE / ICSE / State
    coaching_institute_name: Mapped[str | None]    = mapped_column(String(100))        # Allen / FIITJEE / Local etc.
    family_income:           Mapped[str | None]    = mapped_column(String(20))         # Low / Mid / High
    parent_education:        Mapped[str | None]    = mapped_column(String(30))         # Upto 10th / 12th / Graduate / PG
    location_type:           Mapped[str | None]    = mapped_column(String(20))         # Urban / Semi-Urban / Rural
    attempt_count:           Mapped[int | None]    = mapped_column(Integer)            # 1 or 2
    mental_health_issues:    Mapped[str | None]    = mapped_column(String(5))          # Yes / No
    peer_pressure_level:     Mapped[str | None]    = mapped_column(String(10))         # Low / Medium / High
    admission_taken:         Mapped[str | None]    = mapped_column(String(5))          # Yes / No

    created_at:          Mapped[datetime]       = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_students_batch_active", "batch_id", "is_active"),
        Index("ix_students_faculty_active", "assigned_faculty_id", "is_active"),
    )

    # Relationships
    batch:            Mapped[Batch | None]           = relationship("Batch", back_populates="students")
    assigned_faculty: Mapped[User | None]            = relationship(
        "User", foreign_keys=[assigned_faculty_id], back_populates="assigned_students"
    )
    risk_assessments: Mapped[list[RiskAssessment]]   = relationship(
        "RiskAssessment", back_populates="student", order_by="RiskAssessment.assessed_at", lazy="select"
    )
    mock_tests:       Mapped[list[MockTestResult]]   = relationship(
        "MockTestResult", back_populates="student", order_by="MockTestResult.test_date", lazy="select"
    )
    surveys:          Mapped[list[WeeklySurvey]]     = relationship(
        "WeeklySurvey", back_populates="student", order_by="WeeklySurvey.survey_date", lazy="select"
    )
    alerts:           Mapped[list[Alert]]            = relationship(
        "Alert", foreign_keys="[Alert.student_id]", back_populates="student", lazy="select"
    )
    attendance:       Mapped[list[AttendanceRecord]] = relationship(
        "AttendanceRecord", back_populates="student", order_by="AttendanceRecord.date", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Student id={self.id} code={self.student_code!r} name={self.full_name!r}>"


# ─── MockTestResult ───────────────────────────────────────────────────────────

class MockTestResult(Base):
    """One mock test sitting for a student (minor / major / grand test)."""

    __tablename__ = "mock_test_results"

    id:              Mapped[int]          = mapped_column(Integer, primary_key=True, index=True)
    student_id:      Mapped[int]          = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    test_date:       Mapped[datetime]     = mapped_column(DateTime(timezone=True), nullable=False)
    test_name:       Mapped[str | None]   = mapped_column(String(200))
    test_type:       Mapped[str | None]   = mapped_column(String(30))   # minor | major | grand_test
    total_score:     Mapped[float | None] = mapped_column(Float)         # 0–360
    physics_score:   Mapped[float | None] = mapped_column(Float)         # 0–120
    chemistry_score: Mapped[float | None] = mapped_column(Float)         # 0–120
    maths_score:     Mapped[float | None] = mapped_column(Float)         # 0–120
    percentile:      Mapped[float | None] = mapped_column(Float)         # 0–100
    rank_in_batch:   Mapped[int | None]   = mapped_column(Integer)

    __table_args__ = (
        Index("ix_mock_tests_student_date", "student_id", "test_date"),
    )

    # Relationships
    student: Mapped[Student] = relationship("Student", back_populates="mock_tests")

    def __repr__(self) -> str:
        return (
            f"<MockTestResult id={self.id} student_id={self.student_id} "
            f"date={self.test_date!s:.10} score={self.total_score}>"
        )


# ─── WeeklySurvey ─────────────────────────────────────────────────────────────

class WeeklySurvey(Base):
    """
    Weekly self-reported wellbeing survey.

    Scores are 1–10 integers unless noted.
    sleep_hours_avg and study_hours_per_day are floats.
    """

    __tablename__ = "weekly_surveys"

    id:                     Mapped[int]          = mapped_column(Integer, primary_key=True, index=True)
    student_id:             Mapped[int]          = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    week_number:            Mapped[int | None]   = mapped_column(Integer)           # ISO week 1–53
    survey_date:            Mapped[datetime]     = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    burnout_score:          Mapped[int | None]   = mapped_column(Integer)           # 1–10
    stress_level:           Mapped[int | None]   = mapped_column(Integer)           # 1–10
    sleep_hours_avg:        Mapped[float | None] = mapped_column(Float)             # hours
    study_hours_per_day:    Mapped[float | None] = mapped_column(Float)             # hours
    parental_pressure:      Mapped[int | None]   = mapped_column(Integer)           # 1–10
    peer_comparison_stress: Mapped[int | None]   = mapped_column(Integer)           # 1–10
    motivation_level:       Mapped[int | None]   = mapped_column(Integer)           # 1–10 (higher = more motivated)
    notes:                  Mapped[str | None]   = mapped_column(Text)

    __table_args__ = (
        Index("ix_surveys_student_week", "student_id", "week_number"),
        Index("ix_surveys_student_date", "student_id", "survey_date"),
    )

    # Relationships
    student: Mapped[Student] = relationship("Student", back_populates="surveys")

    def __repr__(self) -> str:
        return (
            f"<WeeklySurvey id={self.id} student_id={self.student_id} "
            f"week={self.week_number} burnout={self.burnout_score}>"
        )


# ─── AttendanceRecord ─────────────────────────────────────────────────────────

class AttendanceRecord(Base):
    """Per-day, per-subject attendance mark (present / absent)."""

    __tablename__ = "attendance_records"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int]      = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    date:       Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    subject:    Mapped[str | None] = mapped_column(String(50))  # Physics / Chemistry / Maths
    present:    Mapped[bool]     = mapped_column(Boolean, nullable=False)

    __table_args__ = (
        Index("ix_attendance_student_date", "student_id", "date"),
        UniqueConstraint("student_id", "date", "subject", name="uq_attendance_student_date_subject"),
    )

    # Relationships
    student: Mapped[Student] = relationship("Student", back_populates="attendance")

    def __repr__(self) -> str:
        status = "P" if self.present else "A"
        return f"<Attendance id={self.id} student_id={self.student_id} date={self.date!s:.10} {status}>"


# ─── RiskAssessment ───────────────────────────────────────────────────────────

class RiskAssessment(Base):
    """
    One ML prediction run for a student.

    feature_snapshot stores the 17 input feature values as JSON so we
    can replay or audit the prediction at any point in the future.
    """

    __tablename__ = "risk_assessments"

    id:               Mapped[int]          = mapped_column(Integer, primary_key=True, index=True)
    student_id:       Mapped[int]          = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    assessed_at:      Mapped[datetime]     = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        index=True,
    )
    risk_score:       Mapped[float | None] = mapped_column(Float)        # 0–100 composite score
    risk_level:       Mapped[str | None]   = mapped_column(String(20), index=True)  # Low/Medium/High/Critical
    ml_probability:   Mapped[float | None] = mapped_column(Float)        # raw model output 0–1
    model_version:    Mapped[str | None]   = mapped_column(String(30))
    feature_snapshot: Mapped[dict | None]  = mapped_column(JSON)         # {feature: value, …}

    __table_args__ = (
        Index("ix_risk_student_at", "student_id", "assessed_at"),
        Index("ix_risk_level_at", "risk_level", "assessed_at"),
    )

    # Relationships
    student:          Mapped[Student]              = relationship("Student", back_populates="risk_assessments")
    shap_explanation: Mapped[ShapExplanation | None] = relationship(
        "ShapExplanation", back_populates="assessment", uselist=False, cascade="all, delete-orphan"
    )
    alert:            Mapped[Alert | None]         = relationship(
        "Alert", back_populates="assessment", uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<RiskAssessment id={self.id} student_id={self.student_id} "
            f"level={self.risk_level!r} score={self.risk_score}>"
        )


# ─── ShapExplanation ──────────────────────────────────────────────────────────

class ShapExplanation(Base):
    """
    SHAP feature-impact data linked to a single RiskAssessment.

    top_factors — JSON list of impact dicts (see SHAPExplainer.explain())
    waterfall_plot — base64-encoded PNG, ready for <img src="data:image/png;base64,…">
    summary_text — human-readable counsellor sentences
    """

    __tablename__ = "shap_explanations"

    id:             Mapped[int]         = mapped_column(Integer, primary_key=True, index=True)
    assessment_id:  Mapped[int]         = mapped_column(
        ForeignKey("risk_assessments.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    base_value:     Mapped[float | None] = mapped_column(Float)
    top_factors:    Mapped[list | None]  = mapped_column(JSON)   # list[dict]
    waterfall_plot: Mapped[str | None]   = mapped_column(Text)   # base64 PNG
    summary_text:   Mapped[str | None]   = mapped_column(Text)   # counsellor sentences

    # Relationships
    assessment: Mapped[RiskAssessment] = relationship("RiskAssessment", back_populates="shap_explanation")

    def __repr__(self) -> str:
        has_plot = self.waterfall_plot is not None
        return f"<ShapExplanation id={self.id} assessment_id={self.assessment_id} plot={has_plot}>"


# ─── Alert ────────────────────────────────────────────────────────────────────

class Alert(Base):
    """
    Counsellor notification generated when risk_level ∈ {Medium, High, Critical}.

    Lifecycle:  created → is_read=True → is_resolved=True
    """

    __tablename__ = "alerts"

    id:              Mapped[int]            = mapped_column(Integer, primary_key=True, index=True)
    student_id:      Mapped[int]            = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id:   Mapped[int | None]     = mapped_column(ForeignKey("risk_assessments.id", ondelete="SET NULL"), index=True)
    assigned_to:     Mapped[int | None]     = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    alert_type:      Mapped[str | None]     = mapped_column(String(50))   # risk_threshold / trend_decline …
    risk_level:      Mapped[str | None]     = mapped_column(String(20), index=True)
    message:         Mapped[str | None]     = mapped_column(Text)
    is_read:         Mapped[bool]           = mapped_column(Boolean, nullable=False, default=False)
    is_resolved:     Mapped[bool]           = mapped_column(Boolean, nullable=False, default=False, index=True)
    resolved_at:     Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_note: Mapped[str | None]     = mapped_column(Text)
    created_at:      Mapped[datetime]       = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_alerts_assignee_resolved", "assigned_to", "is_resolved"),
        Index("ix_alerts_student_created", "student_id", "created_at"),
    )

    # Relationships
    student:    Mapped[Student]              = relationship(
        "Student", foreign_keys=[student_id], back_populates="alerts"
    )
    assessment: Mapped[RiskAssessment | None] = relationship("RiskAssessment", back_populates="alert")
    assignee:   Mapped[User | None]          = relationship(
        "User", foreign_keys=[assigned_to], back_populates="assigned_alerts"
    )

    def __repr__(self) -> str:
        return (
            f"<Alert id={self.id} student_id={self.student_id} "
            f"level={self.risk_level!r} resolved={self.is_resolved}>"
        )


# ─── AuditLog ─────────────────────────────────────────────────────────────────

class AuditLog(Base):
    """
    Immutable record of every state-changing API action.

    Written by middleware / router hooks; never updated or deleted.
    """

    __tablename__ = "audit_logs"

    id:          Mapped[int]         = mapped_column(Integer, primary_key=True, index=True)
    user_id:     Mapped[int | None]  = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action:      Mapped[str]         = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str | None]  = mapped_column(String(50))   # Student / Alert / …
    entity_id:   Mapped[int | None]  = mapped_column(Integer)
    ip_address:  Mapped[str | None]  = mapped_column(String(45))   # supports IPv6
    timestamp:   Mapped[datetime]    = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        index=True,
    )
    details:     Mapped[dict | None] = mapped_column(JSON)          # arbitrary context

    __table_args__ = (
        Index("ix_audit_user_ts", "user_id", "timestamp"),
        Index("ix_audit_entity", "entity_type", "entity_id"),
    )

    # Relationships
    user: Mapped[User | None] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} user_id={self.user_id} "
            f"action={self.action!r} ts={self.timestamp!s:.19}>"
        )


# ─── BlacklistedToken ─────────────────────────────────────────────────────────

class BlacklistedToken(Base):
    """
    Stores invalidated JWT refresh tokens.

    Checked on every /auth/refresh call.
    Rows can be pruned once expires_at < NOW() (cron job / background task).
    """

    __tablename__ = "blacklisted_tokens"

    id:             Mapped[int]            = mapped_column(Integer, primary_key=True, index=True)
    token_jti:      Mapped[str]            = mapped_column(String(200), unique=True, nullable=False, index=True)
    blacklisted_at: Mapped[datetime]       = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    expires_at:     Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    def __repr__(self) -> str:
        return f"<BlacklistedToken id={self.id} jti={self.token_jti[:12]}… exp={self.expires_at!s:.19}>"


# ─── PredictionLog ─────────────────────────────────────────────────────────────

class PredictionLog(Base):
    """
    Immutable log of all ML predictions made through the API.

    Used for auditing, analytics, and debugging model performance over time.
    """

    __tablename__ = "prediction_logs"

    id:                 Mapped[int]            = mapped_column(Integer, primary_key=True, index=True)
    student_id:         Mapped[int]            = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id:            Mapped[int]            = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    user_role:          Mapped[str]            = mapped_column(String(20), nullable=False)
    risk_score:         Mapped[float]          = mapped_column(Float, nullable=False)
    risk_level:         Mapped[str]            = mapped_column(String(20), nullable=False, index=True)
    ml_probability:     Mapped[float]          = mapped_column(Float, nullable=False)
    model_version:      Mapped[str]            = mapped_column(String(50), nullable=False)
    inference_time_ms:  Mapped[float]          = mapped_column(Float, nullable=False)
    feature_snapshot:   Mapped[dict | None]    = mapped_column(JSON)
    timestamp:          Mapped[datetime]       = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_prediction_logs_student_ts", "student_id", "timestamp"),
        Index("ix_prediction_logs_user_ts", "user_id", "timestamp"),
        Index("ix_prediction_logs_risk_level", "risk_level"),
    )

    # Relationships
    student: Mapped[Student] = relationship("Student", foreign_keys=[student_id])
    user:    Mapped[User]    = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return (
            f"<PredictionLog id={self.id} student_id={self.student_id} "
            f"risk={self.risk_level!r} score={self.risk_score:.1f}>"
        )


# ─── Intervention ─────────────────────────────────────────────────────────────

class Intervention(Base):
    """
    AI-generated intervention plan for a student.

    Contains priority, summary, action items, and parent communication draft.
    """

    __tablename__ = "interventions"

    id:              Mapped[int]         = mapped_column(Integer, primary_key=True, index=True)
    student_id:      Mapped[int]         = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by:      Mapped[int]         = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    created_at:      Mapped[datetime]    = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        index=True,
    )
    priority:        Mapped[str]         = mapped_column(String(20), nullable=False, index=True)  # high / medium / low
    summary:         Mapped[str | None]  = mapped_column(Text)
    actions:         Mapped[list | None]  = mapped_column(JSON)  # list of action dicts
    parent_message:  Mapped[str | None]  = mapped_column(Text)
    status:          Mapped[str]         = mapped_column(String(20), nullable=False, default="pending", index=True)  # pending / in_progress / completed
    completed_at:    Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_interventions_student_status", "student_id", "status"),
        Index("ix_interventions_created_at", "created_at"),
    )

    # Relationships
    student:    Mapped[Student] = relationship("Student", foreign_keys=[student_id])
    creator:    Mapped[User]    = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return (
            f"<Intervention id={self.id} student_id={self.student_id} "
            f"priority={self.priority!r} status={self.status!r}>"
        )
