"""
models/student.py
─────────────────
Student model for JEE aspirants.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Float, Integer, String, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class Student(Base):
    """JEE aspirant enrolled in a coaching batch."""

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_code: Mapped[str | None] = mapped_column(String(30), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("batches.id", ondelete="SET NULL"), index=True)
    assigned_faculty_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    enrollment_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    target_rank: Mapped[int | None] = mapped_column(Integer)
    target_college: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # Real-dataset profile fields
    jee_main_score: Mapped[float | None] = mapped_column(Float)
    jee_advanced_score: Mapped[float | None] = mapped_column(Float)
    school_board: Mapped[str | None] = mapped_column(String(20))
    coaching_institute_name: Mapped[str | None] = mapped_column(String(100))
    family_income: Mapped[str | None] = mapped_column(String(20))
    parent_education: Mapped[str | None] = mapped_column(String(30))
    location_type: Mapped[str | None] = mapped_column(String(20))
    attempt_count: Mapped[int | None] = mapped_column(Integer)
    mental_health_issues: Mapped[str | None] = mapped_column(String(5))
    peer_pressure_level: Mapped[str | None] = mapped_column(String(10))
    admission_taken: Mapped[str | None] = mapped_column(String(5))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_students_batch_active", "batch_id", "is_active"),
        Index("ix_students_faculty_active", "assigned_faculty_id", "is_active"),
    )

    # Relationships
    assigned_faculty: Mapped[Any | None] = relationship(
        "User", foreign_keys=[assigned_faculty_id], back_populates="assigned_students"
    )
    risk_assessments: Mapped[list[Any]] = relationship(
        "RiskAssessment", back_populates="student", order_by="RiskAssessment.assessed_at", lazy="select"
    )
    alerts: Mapped[list[Any]] = relationship(
        "Alert", foreign_keys="[Alert.student_id]", back_populates="student", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Student id={self.id} code={self.student_code!r} name={self.full_name!r}>"
