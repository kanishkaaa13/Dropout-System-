"""
backend/app/middleware/rbac.py
───────────────────────────────
Fine-grained Role-Based Access Control helpers.

Beyond the coarse role checks in auth.py, this module provides:
  - require_role(*roles)                — decorator / Depends factory
  - verify_student_access(student, user) — faculty can only see assigned students
  - verify_own_data(student_id, user)   — students can only see themselves

Usage
─────
    from backend.app.middleware.rbac import require_role, verify_student_access

    @router.get("/admin-only")
    def admin_endpoint(user: User = Depends(require_role("admin"))):
        ...

    @router.get("/students/{id}")
    def student_detail(student: Student = Depends(get_student), ...):
        verify_student_access(student, current_user)
        ...
"""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database        import get_db
from backend.app.middleware.auth import get_current_user
from backend.app.models.database import Student, User

log = logging.getLogger(__name__)

# ── Role requirement factory ──────────────────────────────────────────────────

def require_role(*roles: str) -> Callable[..., User]:
    """
    FastAPI Depends factory.  Returns a dependency that verifies the current
    user's role is in *roles*.

    Example
    -------
        @router.delete("/students/{id}")
        def delete_student(user: User = Depends(require_role("admin"))):
            ...
    """
    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            log.warning(
                "RBAC: user %s (role=%s) attempted access requiring %s",
                current_user.email, current_user.role, roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of the following roles: {', '.join(roles)}.",
            )
        return current_user

    return _dependency


# ── Student-level access checks ───────────────────────────────────────────────

def verify_student_access(student: Student, current_user: User) -> None:
    """
    Enforce that a faculty member can only access students assigned to them.
    Admin can access any student.

    Raises
    ------
    HTTPException 403  — faculty accessing unassigned student
    """
    if current_user.role == "admin":
        return

    if current_user.role == "faculty":
        if student.assigned_faculty_id != current_user.id:
            log.warning(
                "RBAC: faculty %d tried to access student %d (assigned to %s)",
                current_user.id, student.id, student.assigned_faculty_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this student.",
            )
        return

    # Any other role (e.g. 'student') must match their own record
    verify_own_data(student.id, current_user)


def verify_own_data(student_id: int, current_user: User) -> None:
    """
    Students may only access their own data.
    Admins and faculty bypass this check.

    Raises
    ------
    HTTPException 403  — student accessing another student's data
    """
    if current_user.role in ("admin", "faculty"):
        return

    # For roles == 'student', the user row should have a linked student_id
    linked_id = getattr(current_user, "student_id", None)
    if linked_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own data.",
        )


# ── Batch-level access check ──────────────────────────────────────────────────

def verify_batch_access(batch_id: int, current_user: User, db: Session) -> None:
    """
    Faculty may only access batches that contain at least one of their students.
    Admin can access any batch.

    Raises
    ------
    HTTPException 403  — faculty accessing batch they have no students in
    """
    if current_user.role == "admin":
        return

    assigned = (
        db.query(Student)
        .filter(
            Student.batch_id            == batch_id,
            Student.assigned_faculty_id == current_user.id,
        )
        .first()
    )
    if not assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have students in this batch.",
        )
