"""
models/alert.py
──────────────
Alert model for counsellor notifications.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class Alert(Base):
    """
    Counsellor notification generated when risk_level ∈ {Medium, High, Critical}.

    Lifecycle: created → is_read=True → is_resolved=True
    """

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id: Mapped[int | None] = mapped_column(ForeignKey("risk_assessments.id", ondelete="SET NULL"), index=True)
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    alert_type: Mapped[str | None] = mapped_column(String(50))  # risk_threshold / trend_decline …
    risk_level: Mapped[str | None] = mapped_column(String(20), index=True)
    message: Mapped[str | None] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
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
    student: Mapped[Any] = relationship(
        "Student", foreign_keys=[student_id], back_populates="alerts"
    )
    assessment: Mapped[Any | None] = relationship("RiskAssessment", back_populates="alert")
    assignee: Mapped[Any | None] = relationship(
        "User", foreign_keys=[assigned_to], back_populates="assigned_alerts"
    )

    def __repr__(self) -> str:
        return (
            f"<Alert id={self.id} student_id={self.student_id} "
            f"level={self.risk_level!r} resolved={self.is_resolved}>"
        )
