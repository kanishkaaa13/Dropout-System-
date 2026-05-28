"""
models/user.py
──────────────
User model for admin and faculty accounts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class User(Base):
    """
    Admin or faculty account.

    Roles
    -----
    admin   — full access to all institutes / batches
    faculty — access limited to their assigned students
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="faculty", index=True)
    institute_id: Mapped[int | None] = mapped_column(ForeignKey("institutes.id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    assigned_students: Mapped[list[Any]] = relationship(
        "Student", foreign_keys="[Student.assigned_faculty_id]", back_populates="assigned_faculty", lazy="select"
    )
    audit_logs: Mapped[list[Any]] = relationship("AuditLog", back_populates="user", lazy="select")
    assigned_alerts: Mapped[list[Any]] = relationship(
        "Alert", foreign_keys="[Alert.assigned_to]", back_populates="assignee", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
