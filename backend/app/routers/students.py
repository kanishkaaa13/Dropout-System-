"""
routers/students.py
───────────────────
Student management endpoints with RBAC.

  GET    /students              — paginated list (admin: all, faculty: assigned only)
  POST   /students              — create student (admin only)
  GET    /students/{id}         — full profile
  PUT    /students/{id}         — update (admin only)
  POST   /students/{id}/mock-tests  — add mock test
  GET    /students/{id}/mock-tests  — list mock tests
  POST   /students/{id}/surveys     — submit weekly survey
  GET    /students/{id}/risk-history — risk score trend
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.middleware.auth import (
    get_admin_user,
    get_current_user,
    get_faculty_or_admin,
)
from backend.app.models.database import (
    MockTestResult,
    RiskAssessment,
    Student,
    User,
    WeeklySurvey,
)
from backend.app.schemas.students import (
    MockTestCreate,
    MockTestOut,
    RiskHistoryPoint,
    RiskSummary,
    StudentCreate,
    StudentListResponse,
    StudentOut,
    StudentUpdate,
    SurveyCreate,
    SurveyOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/students", tags=["Students"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_student_or_404(student_id: int, db: Session) -> Student:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id={student_id} not found.",
        )
    return student


def _enrich_student(student: Student) -> StudentOut:
    """Attach the latest risk assessment summary to a StudentOut schema."""
    latest = (
        student.risk_assessments[-1]
        if student.risk_assessments
        else None
    )
    out = StudentOut.model_validate(student)
    if latest:
        out.latest_risk = RiskSummary(
            risk_score  = latest.risk_score,
            risk_level  = latest.risk_level,
            assessed_at = latest.assessed_at,
        )
    return out


# ── GET /students ─────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=StudentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List students (paginated)",
)
def list_students(
    page:        int         = Query(1,    ge=1,  description="Page number"),
    size:        int         = Query(20,   ge=1, le=100, description="Items per page"),
    search:      str | None  = Query(None, description="Search by name or student_code"),
    risk_level:  str | None  = Query(None, description="Filter by risk level: Low/Medium/High/Critical"),
    batch_id:    int | None  = Query(None, description="Filter by batch ID"),
    current_user: User   = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> StudentListResponse:
    """
    Return a paginated list of students.

    - **Admin**: sees all students across the institute.
    - **Faculty**: sees only their assigned students.
    """
    query = db.query(Student).filter(Student.is_active == True)  # noqa: E712

    # RBAC filter
    if current_user.role == "faculty":
        query = query.filter(Student.assigned_faculty_id == current_user.id)

    # Optional filters
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            Student.full_name.ilike(pattern)
            | Student.student_code.ilike(pattern)
        )
    if batch_id is not None:
        query = query.filter(Student.batch_id == batch_id)

    # Risk level filter via subquery on latest assessment
    if risk_level:
        from sqlalchemy import select as _select
        subq = (
            _select(RiskAssessment.student_id)
            .where(RiskAssessment.risk_level == risk_level)
        )
        query = query.filter(Student.id.in_(subq))

    total = query.count()
    pages = max(1, math.ceil(total / size))

    students = (
        query
        .order_by(Student.full_name)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return StudentListResponse(
        items=[_enrich_student(s) for s in students],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


# ── POST /students ────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=StudentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new student (admin only)",
)
def create_student(
    body:         StudentCreate,
    current_user: User    = Depends(get_admin_user),
    db:           Session = Depends(get_db),
) -> StudentOut:
    """Create a single student record. Requires admin role."""
    if body.email:
        exists = db.query(Student).filter(Student.email == body.email).first()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A student with email '{body.email}' already exists.",
            )

    student = Student(**body.model_dump(exclude_none=True))
    db.add(student)
    db.commit()
    db.refresh(student)

    logger.info("Admin %s created student id=%d.", current_user.email, student.id)
    return StudentOut.model_validate(student)


# ── GET /students/{id} ────────────────────────────────────────────────────────

@router.get(
    "/{student_id}",
    response_model=StudentOut,
    status_code=status.HTTP_200_OK,
    summary="Get full student profile",
)
def get_student(
    student_id:   int,
    current_user: User    = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> StudentOut:
    """
    Retrieve a student's full profile.
    Faculty can only view their own assigned students.
    """
    student = _get_student_or_404(student_id, db)

    if (
        current_user.role == "faculty"
        and student.assigned_faculty_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this student.",
        )

    return _enrich_student(student)


# ── PUT /students/{id} ────────────────────────────────────────────────────────

@router.put(
    "/{student_id}",
    response_model=StudentOut,
    status_code=status.HTTP_200_OK,
    summary="Update a student (admin only)",
)
def update_student(
    student_id:   int,
    body:         StudentUpdate,
    current_user: User    = Depends(get_admin_user),
    db:           Session = Depends(get_db),
) -> StudentOut:
    """Update any student field.  Requires admin role."""
    student = _get_student_or_404(student_id, db)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)

    logger.info("Admin %s updated student id=%d.", current_user.email, student_id)
    return _enrich_student(student)


# ── POST /students/{id}/mock-tests ────────────────────────────────────────────

@router.post(
    "/{student_id}/mock-tests",
    response_model=MockTestOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a mock test result",
)
def add_mock_test(
    student_id:   int,
    body:         MockTestCreate,
    current_user: User    = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> MockTestOut:
    """
    Record a mock test result for a student.
    Faculty must be assigned to the student.
    """
    student = _get_student_or_404(student_id, db)

    if (
        current_user.role == "faculty"
        and student.assigned_faculty_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this student.",
        )

    result = MockTestResult(student_id=student_id, **body.model_dump())
    db.add(result)
    db.commit()
    db.refresh(result)

    logger.info("Mock test added for student id=%d by %s.", student_id, current_user.email)
    return MockTestOut.model_validate(result)


# ── GET /students/{id}/mock-tests ─────────────────────────────────────────────

@router.get(
    "/{student_id}/mock-tests",
    response_model=list[MockTestOut],
    status_code=status.HTTP_200_OK,
    summary="List mock test results (chronological)",
)
def list_mock_tests(
    student_id:   int,
    current_user: User    = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> list[MockTestOut]:
    """Return all mock test results for a student, sorted oldest-first."""
    _get_student_or_404(student_id, db)

    rows = (
        db.query(MockTestResult)
        .filter(MockTestResult.student_id == student_id)
        .order_by(MockTestResult.test_date.asc())
        .all()
    )
    return [MockTestOut.model_validate(r) for r in rows]


# ── POST /students/{id}/surveys ───────────────────────────────────────────────

@router.post(
    "/{student_id}/surveys",
    response_model=SurveyOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a weekly self-assessment survey",
)
def submit_survey(
    student_id:   int,
    body:         SurveyCreate,
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db),
) -> SurveyOut:
    """
    Submit a weekly survey for a student.
    Students can submit their own; faculty/admin can submit for any assigned student.
    """
    student = _get_student_or_404(student_id, db)

    # Faculty RBAC
    if current_user.role == "faculty" and student.assigned_faculty_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this student.",
        )

    now = datetime.now(timezone.utc)
    # Compute ISO week number
    week_number = now.isocalendar()[1]

    survey = WeeklySurvey(
        student_id=student_id,
        survey_date=now,
        week_number=week_number,
        **body.model_dump(),
    )
    db.add(survey)
    db.commit()
    db.refresh(survey)

    logger.info("Survey submitted for student id=%d.", student_id)
    return SurveyOut.model_validate(survey)


# ── GET /students/{id}/risk-history ───────────────────────────────────────────

@router.get(
    "/{student_id}/risk-history",
    response_model=list[RiskHistoryPoint],
    status_code=status.HTTP_200_OK,
    summary="Get risk score history for trend charts",
)
def get_risk_history(
    student_id:   int,
    limit:        int  = Query(20, ge=1, le=100, description="Max assessments to return"),
    current_user: User    = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> list[RiskHistoryPoint]:
    """
    Return chronological risk assessment history for a student.
    Used to plot the risk score trend chart on the frontend.
    """
    _get_student_or_404(student_id, db)

    rows = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.student_id == student_id)
        .order_by(RiskAssessment.assessed_at.asc())
        .limit(limit)
        .all()
    )
    return [RiskHistoryPoint.model_validate(r) for r in rows]
