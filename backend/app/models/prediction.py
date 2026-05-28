"""
models/prediction.py
───────────────────
Prediction-related models: RiskAssessment and ShapExplanation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Float, Integer, JSON, String, Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class RiskAssessment(Base):
    """
    One ML prediction run for a student.

    feature_snapshot stores the 17 input feature values as JSON so we
    can replay or audit the prediction at any point in the future.
    """

    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        index=True,
    )
    risk_score: Mapped[float | None] = mapped_column(Float)  # 0–100 composite score
    risk_level: Mapped[str | None] = mapped_column(String(20), index=True)  # Low/Medium/High/Critical
    ml_probability: Mapped[float | None] = mapped_column(Float)  # raw model output 0–1
    model_version: Mapped[str | None] = mapped_column(String(30))
    feature_snapshot: Mapped[dict | None] = mapped_column(JSON)  # {feature: value, …}

    __table_args__ = (
        Index("ix_risk_student_at", "student_id", "assessed_at"),
        Index("ix_risk_level_at", "risk_level", "assessed_at"),
    )

    # Relationships
    student: Mapped[Any] = relationship("Student", back_populates="risk_assessments")
    shap_explanation: Mapped[Any | None] = relationship(
        "ShapExplanation", back_populates="assessment", uselist=False, cascade="all, delete-orphan"
    )
    alert: Mapped[Any | None] = relationship(
        "Alert", back_populates="assessment", uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<RiskAssessment id={self.id} student_id={self.student_id} "
            f"level={self.risk_level!r} score={self.risk_score}>"
        )


class ShapExplanation(Base):
    """
    SHAP feature-impact data linked to a single RiskAssessment.

    top_factors — JSON list of impact dicts (see SHAPExplainer.explain())
    waterfall_plot — base64-encoded PNG, ready for <img src="data:image/png;base64,…">
    summary_text — human-readable counsellor sentences
    """

    __tablename__ = "shap_explanations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("risk_assessments.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    base_value: Mapped[float | None] = mapped_column(Float)
    top_factors: Mapped[list | None] = mapped_column(JSON)  # list[dict]
    waterfall_plot: Mapped[str | None] = mapped_column(Text)  # base64 PNG
    summary_text: Mapped[str | None] = mapped_column(Text)  # counsellor sentences

    # Relationships
    assessment: Mapped[RiskAssessment] = relationship("RiskAssessment", back_populates="shap_explanation")

    def __repr__(self) -> str:
        has_plot = self.waterfall_plot is not None
        return f"<ShapExplanation id={self.id} assessment_id={self.assessment_id} plot={has_plot}>"
