"""
routers/demo.py
──────────────
Demo Mode endpoints for presentations.

  POST /api/demo/seed  — Insert 15 realistic fake students
  DELETE /api/demo/reset — Clear demo data
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.middleware.auth import get_admin
from backend.app.models.database import (
    AttendanceRecord,
    Batch,
    Institute,
    MockTestResult,
    RiskAssessment,
    Student,
    User,
    WeeklySurvey,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["Demo"])


# ── Demo student data ───────────────────────────────────────────────────────────

DEMO_STUDENTS = [
    # High Risk (3 students)
    {
        "name": "Priya S.",
        "email": "priya.s.demo@example.com",
        "phone": "9876543210",
        "risk_level": "High",
        "risk_score": 78,
        "attendance": 45,
        "physics_score": 42,
        "chemistry_score": 38,
        "maths_score": 35,
        "stress_level": 9,
        "burnout_score": 8,
        "sleep_hours": 4.5,
        "study_hours": 12,
        "mock_avg": 135,
    },
    {
        "name": "Rahul K.",
        "email": "rahul.k.demo@example.com",
        "phone": "9876543211",
        "risk_level": "High",
        "risk_score": 82,
        "attendance": 38,
        "physics_score": 40,
        "chemistry_score": 35,
        "maths_score": 32,
        "stress_level": 10,
        "burnout_score": 9,
        "sleep_hours": 4.0,
        "study_hours": 14,
        "mock_avg": 128,
    },
    {
        "name": "Sneha P.",
        "email": "sneha.p.demo@example.com",
        "phone": "9876543212",
        "risk_level": "High",
        "risk_score": 75,
        "attendance": 50,
        "physics_score": 45,
        "chemistry_score": 40,
        "maths_score": 38,
        "stress_level": 8,
        "burnout_score": 7,
        "sleep_hours": 5.0,
        "study_hours": 11,
        "mock_avg": 142,
    },
    # Medium Risk (5 students)
    {
        "name": "Rohan M.",
        "email": "rohan.m.demo@example.com",
        "phone": "9876543213",
        "risk_level": "Medium",
        "risk_score": 55,
        "attendance": 70,
        "physics_score": 58,
        "chemistry_score": 55,
        "maths_score": 52,
        "stress_level": 6,
        "burnout_score": 5,
        "sleep_hours": 6.0,
        "study_hours": 9,
        "mock_avg": 168,
    },
    {
        "name": "Anjali K.",
        "email": "anjali.k.demo@example.com",
        "phone": "9876543214",
        "risk_level": "Medium",
        "risk_score": 52,
        "attendance": 75,
        "physics_score": 60,
        "chemistry_score": 58,
        "maths_score": 55,
        "stress_level": 5,
        "burnout_score": 4,
        "sleep_hours": 6.5,
        "study_hours": 8,
        "mock_avg": 172,
    },
    {
        "name": "Vikram S.",
        "email": "vikram.s.demo@example.com",
        "phone": "9876543215",
        "risk_level": "Medium",
        "risk_score": 58,
        "attendance": 68,
        "physics_score": 56,
        "chemistry_score": 54,
        "maths_score": 50,
        "stress_level": 7,
        "burnout_score": 6,
        "sleep_hours": 5.5,
        "study_hours": 10,
        "mock_avg": 165,
    },
    {
        "name": "Meera R.",
        "email": "meera.r.demo@example.com",
        "phone": "9876543216",
        "risk_level": "Medium",
        "risk_score": 50,
        "attendance": 72,
        "physics_score": 62,
        "chemistry_score": 56,
        "maths_score": 54,
        "stress_level": 5,
        "burnout_score": 5,
        "sleep_hours": 7.0,
        "study_hours": 8,
        "mock_avg": 175,
    },
    {
        "name": "Arjun T.",
        "email": "arjun.t.demo@example.com",
        "phone": "9876543217",
        "risk_level": "Medium",
        "risk_score": 54,
        "attendance": 65,
        "physics_score": 55,
        "chemistry_score": 52,
        "maths_score": 53,
        "stress_level": 6,
        "burnout_score": 5,
        "sleep_hours": 6.0,
        "study_hours": 9,
        "mock_avg": 170,
    },
    # Low Risk (7 students)
    {
        "name": "Anjali K.",
        "email": "anjali.k2.demo@example.com",
        "phone": "9876543218",
        "risk_level": "Low",
        "risk_score": 25,
        "attendance": 92,
        "physics_score": 78,
        "chemistry_score": 75,
        "maths_score": 82,
        "stress_level": 3,
        "burnout_score": 2,
        "sleep_hours": 7.5,
        "study_hours": 7,
        "mock_avg": 245,
    },
    {
        "name": "Deepak N.",
        "email": "deepak.n.demo@example.com",
        "phone": "9876543219",
        "risk_level": "Low",
        "risk_score": 22,
        "attendance": 95,
        "physics_score": 80,
        "chemistry_score": 78,
        "maths_score": 85,
        "stress_level": 2,
        "burnout_score": 2,
        "sleep_hours": 8.0,
        "study_hours": 6,
        "mock_avg": 252,
    },
    {
        "name": "Kavita S.",
        "email": "kavita.s.demo@example.com",
        "phone": "9876543220",
        "risk_level": "Low",
        "risk_score": 28,
        "attendance": 88,
        "physics_score": 75,
        "chemistry_score": 72,
        "maths_score": 78,
        "stress_level": 4,
        "burnout_score": 3,
        "sleep_hours": 7.0,
        "study_hours": 8,
        "mock_avg": 238,
    },
    {
        "name": "Nikhil P.",
        "email": "nikhil.p.demo@example.com",
        "phone": "9876543221",
        "risk_level": "Low",
        "risk_score": 20,
        "attendance": 94,
        "physics_score": 82,
        "chemistry_score": 80,
        "maths_score": 88,
        "stress_level": 2,
        "burnout_score": 1,
        "sleep_hours": 8.5,
        "study_hours": 6,
        "mock_avg": 258,
    },
    {
        "name": "Pooja M.",
        "email": "pooja.m.demo@example.com",
        "phone": "9876543222",
        "risk_level": "Low",
        "risk_score": 30,
        "attendance": 85,
        "physics_score": 72,
        "chemistry_score": 70,
        "maths_score": 75,
        "stress_level": 4,
        "burnout_score": 3,
        "sleep_hours": 7.0,
        "study_hours": 8,
        "mock_avg": 230,
    },
    {
        "name": "Saurabh J.",
        "email": "saurabh.j.demo@example.com",
        "phone": "9876543223",
        "risk_level": "Low",
        "risk_score": 24,
        "attendance": 90,
        "physics_score": 76,
        "chemistry_score": 74,
        "maths_score": 80,
        "stress_level": 3,
        "burnout_score": 2,
        "sleep_hours": 7.5,
        "study_hours": 7,
        "mock_avg": 242,
    },
    {
        "name": "Divya R.",
        "email": "divya.r.demo@example.com",
        "phone": "9876543224",
        "risk_level": "Low",
        "risk_score": 26,
        "attendance": 89,
        "physics_score": 74,
        "chemistry_score": 73,
        "maths_score": 77,
        "stress_level": 3,
        "burnout_score": 2,
        "sleep_hours": 7.5,
        "study_hours": 7,
        "mock_avg": 240,
    },
]


# ── POST /api/demo/seed ─────────────────────────────────────────────────────────

@router.post(
    "/seed",
    status_code=status.HTTP_201_CREATED,
    summary="Seed demo students for presentations",
)
async def seed_demo_data(
    current_user: User = Depends(get_admin),
    db: Session = Depends(get_db),
) -> dict:
    """
    Insert 15 realistic fake students with varied risk profiles.
    
    Creates:
    - 3 high risk students
    - 5 medium risk students
    - 7 low risk students
    
    Each student gets:
    - Attendance records
    - Mock test results
    - Weekly surveys
    - Risk assessments
    """
    # Get or create demo institute and batch
    institute = db.query(Institute).filter(Institute.code == "DEMO").first()
    if not institute:
        institute = Institute(
            name="Demo Institute",
            code="DEMO",
            city="Demo City",
        )
        db.add(institute)
        db.flush()
    
    batch = db.query(Batch).filter(Batch.name == "Demo Batch 2025").first()
    if not batch:
        batch = Batch(
            institute_id=institute.id,
            name="Demo Batch 2025",
            year=2025,
            shift="morning",
            target_exam="JEE_MAIN",
        )
        db.add(batch)
        db.flush()
    
    # Get a demo faculty user
    faculty = db.query(User).filter(User.email == "demo.faculty@example.com").first()
    if not faculty:
        faculty = User(
            email="demo.faculty@example.com",
            hashed_password="demo_hash",  # Not used for demo
            full_name="Demo Faculty",
            role="faculty",
            institute_id=institute.id,
        )
        db.add(faculty)
        db.flush()
    
    # Clear existing demo data
    db.query(Student).filter(Student.is_demo == True).delete()
    db.query(AttendanceRecord).filter(Student.is_demo == True).delete(synchronize_session=False)
    db.query(MockTestResult).filter(Student.is_demo == True).delete(synchronize_session=False)
    db.query(WeeklySurvey).filter(Student.is_demo == True).delete(synchronize_session=False)
    db.query(RiskAssessment).filter(Student.is_demo == True).delete(synchronize_session=False)
    
    created_students = []
    base_date = datetime.now(timezone.utc) - timedelta(days=90)
    
    for i, student_data in enumerate(DEMO_STUDENTS):
        # Create student
        student = Student(
            student_code=f"DEMO{i+1:03d}",
            full_name=student_data["name"],
            email=student_data["email"],
            phone=student_data["phone"],
            batch_id=batch.id,
            assigned_faculty_id=faculty.id,
            enrollment_date=base_date,
            target_rank=500,
            target_college="IIT Bombay",
            is_active=True,
            is_demo=True,
        )
        db.add(student)
        db.flush()
        
        created_students.append(student.id)
        
        # Create attendance records (last 30 days)
        for day in range(30):
            date = base_date + timedelta(days=day)
            attendance_rate = student_data["attendance"] / 100
            
            for subject in ["Physics", "Chemistry", "Maths"]:
                present = (hash(f"{student.id}{date}{subject}") % 100) < (attendance_rate * 100)
                attendance = AttendanceRecord(
                    student_id=student.id,
                    date=date,
                    subject=subject,
                    present=present,
                )
                db.add(attendance)
        
        # Create mock test results (5 tests)
        for test_num in range(1, 6):
            test_date = base_date + timedelta(days=test_num * 14)
            base_score = student_data["mock_avg"]
            variation = (hash(f"{student.id}{test_num}") % 20) - 10
            
            mock = MockTestResult(
                student_id=student.id,
                test_date=test_date,
                test_name=f"Mock Test {test_num}",
                test_type="major",
                total_score=base_score + variation,
                physics_score=student_data["physics_score"] + variation // 3,
                chemistry_score=student_data["chemistry_score"] + variation // 3,
                maths_score=student_data["maths_score"] + variation // 3,
                percentile=(base_score + variation) / 360 * 100,
                rank_in_batch=hash(f"{student.id}{test_num}") % 50 + 1,
            )
            db.add(mock)
        
        # Create weekly surveys (last 8 weeks)
        for week in range(8):
            survey_date = base_date + timedelta(weeks=week)
            survey = WeeklySurvey(
                student_id=student.id,
                week_number=week + 1,
                survey_date=survey_date,
                burnout_score=student_data["burnout_score"],
                stress_level=student_data["stress_level"],
                sleep_hours_avg=student_data["sleep_hours"],
                study_hours_per_day=student_data["study_hours"],
                parental_pressure=5,
                peer_comparison_stress=5,
                motivation_level=7,
            )
            db.add(survey)
        
        # Create risk assessment
        assessment = RiskAssessment(
            student_id=student.id,
            assessed_at=datetime.now(timezone.utc),
            risk_score=student_data["risk_score"],
            risk_level=student_data["risk_level"],
            ml_probability=student_data["risk_score"] / 100,
            model_version="1.0.0",
            feature_snapshot={
                "attendance_rate": student_data["attendance"],
                "mock_test_avg": student_data["mock_avg"],
                "physics_score": student_data["physics_score"],
                "chemistry_score": student_data["chemistry_score"],
                "maths_score": student_data["maths_score"],
                "burnout_score": student_data["burnout_score"],
                "stress_level": student_data["stress_level"],
                "sleep_hours_avg": student_data["sleep_hours"],
                "study_hours_per_day": student_data["study_hours"],
            },
        )
        db.add(assessment)
    
    db.commit()
    
    logger.info(f"Seeded {len(DEMO_STUDENTS)} demo students")
    
    return {
        "message": f"Seeded {len(DEMO_STUDENTS)} demo students",
        "students": len(DEMO_STUDENTS),
        "high_risk": 3,
        "medium_risk": 5,
        "low_risk": 7,
    }


# ── DELETE /api/demo/reset ───────────────────────────────────────────────────────

@router.delete(
    "/reset",
    status_code=status.HTTP_200_OK,
    summary="Clear all demo data",
)
async def reset_demo_data(
    current_user: User = Depends(get_admin),
    db: Session = Depends(get_db),
) -> dict:
    """
    Delete all demo students and their associated data.
    """
    # Count before deletion
    demo_count = db.query(Student).filter(Student.is_demo == True).count()
    
    # Delete demo data (cascade will handle related records)
    db.query(Student).filter(Student.is_demo == True).delete()
    
    db.commit()
    
    logger.info(f"Reset demo data: deleted {demo_count} students")
    
    return {
        "message": f"Deleted {demo_count} demo students",
        "deleted": demo_count,
    }
