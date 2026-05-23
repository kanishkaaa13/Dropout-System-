"""
backend/app/routers/reports.py
────────────────────────────────
PDF and Excel report download endpoints.

Routes
──────
  GET /reports/student/{student_id}/pdf        — single student PDF
  GET /reports/batch/{batch_id}/excel          — full batch Excel workbook
"""

from __future__ import annotations

import logging
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from backend.app.database         import get_db
from backend.app.middleware.auth  import get_current_user, get_faculty_or_admin
from backend.app.models.database  import (
    Student, RiskAssessment, ShapExplanation, MockTestResult, Batch, User
)
from backend.app.services.report_service import generate_student_pdf, generate_batch_excel

log    = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _check_student_access(student: Student, current_user: User) -> None:
    """Faculty may only access reports for students assigned to them."""
    if current_user.role == "faculty" and student.assigned_faculty_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorised to download reports for this student",
        )


def _check_batch_access(batch: Batch, current_user: User, db: Session) -> None:
    """Faculty may only download reports for batches that contain their students."""
    if current_user.role == "admin":
        return
    assigned = (
        db.query(Student)
        .filter_by(batch_id=batch.id, assigned_faculty_id=current_user.id)
        .first()
    )
    if not assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorised to download reports for this batch",
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/student/{student_id}/pdf",
    summary="Download student risk report (PDF)",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF report as binary download",
        }
    },
)
def student_pdf_report(
    student_id:   int,
    current_user: User    = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> StreamingResponse:
    # ── Fetch student ─────────────────────────────────────────────────────────
    student: Student | None = db.query(Student).filter_by(id=student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    _check_student_access(student, current_user)

    # ── Latest assessment + SHAP explanation ──────────────────────────────────
    latest_assessment: RiskAssessment | None = (
        db.query(RiskAssessment)
        .filter_by(student_id=student_id)
        .order_by(RiskAssessment.assessed_at.desc())
        .first()
    )

    shap_explanation: ShapExplanation | None = None
    if latest_assessment:
        shap_explanation = (
            db.query(ShapExplanation)
            .filter_by(assessment_id=latest_assessment.id)
            .first()
        )

    # ── Mock tests (last 5) ───────────────────────────────────────────────────
    mock_tests = (
        db.query(MockTestResult)
        .filter_by(student_id=student_id)
        .order_by(MockTestResult.test_date.desc())
        .limit(5)
        .all()
    )

    # ── Resolve institute name ────────────────────────────────────────────────
    institute_name = "JEE Coaching Institute"
    if student.batch and student.batch.institute:
        institute_name = student.batch.institute.name

    # ── Generate PDF ──────────────────────────────────────────────────────────
    try:
        pdf_bytes = generate_student_pdf(
            student           = student,
            latest_assessment = latest_assessment,
            shap_explanation  = shap_explanation,
            mock_tests        = mock_tests,
            institute_name    = institute_name,
        )
    except Exception as exc:
        log.exception("PDF generation failed for student_id=%d: %s", student_id, exc)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    filename = f"student_{student.student_code or student_id}_report.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/batch/{batch_id}/excel",
    summary="Download batch risk summary (Excel)",
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
            },
            "description": "Excel workbook as binary download",
        }
    },
)
def batch_excel_report(
    batch_id:     int,
    current_user: User    = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> StreamingResponse:
    # ── Fetch batch ───────────────────────────────────────────────────────────
    batch: Batch | None = (
        db.query(Batch)
        .options(joinedload(Batch.institute))
        .filter_by(id=batch_id)
        .first()
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    _check_batch_access(batch, current_user, db)

    # ── Fetch all students + eager-load assessments ───────────────────────────
    students = (
        db.query(Student)
        .options(
            joinedload(Student.risk_assessments).joinedload(RiskAssessment.shap_explanations),
        )
        .filter_by(batch_id=batch_id, is_active=True)
        .order_by(Student.full_name)
        .all()
    )

    if not students:
        raise HTTPException(
            status_code=404,
            detail="No active students found in this batch",
        )

    # ── Generate Excel ────────────────────────────────────────────────────────
    try:
        xlsx_bytes = generate_batch_excel(batch_id=batch_id, students=students)
    except Exception as exc:
        log.exception("Excel generation failed for batch_id=%d: %s", batch_id, exc)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    batch_code = batch.name.replace(" ", "_") if batch.name else str(batch_id)
    filename   = f"batch_{batch_code}_risk_report.xlsx"
    return StreamingResponse(
        BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
