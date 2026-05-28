"""
routers/interventions.py
───────────────────────
AI Intervention Recommendation Engine endpoints.

  POST /api/students/{id}/interventions/generate  — Generate AI intervention plan
  GET  /api/students/{id}/interventions            — Fetch intervention history
  PATCH /api/interventions/{id}/complete          — Mark intervention as complete
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.middleware.auth import get_faculty_or_admin
from backend.app.models.database import Intervention, Student, User
from backend.app.schemas.intervention import (
    ActionItem,
    CompleteActionRequest,
    CompleteActionResponse,
    GenerateInterventionRequest,
    GenerateInterventionResponse,
    InterventionListResponse,
    InterventionListItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interventions", tags=["Interventions"])

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3"


# ── Helper: Generate AI intervention plan using Ollama ─────────────────────────

async def generate_ai_intervention(
    student_name: str,
    risk_factors: dict,
    risk_score: float,
    risk_level: str,
) -> dict:
    """
    Call Ollama (llama3) to generate intervention recommendations.
    
    Returns structured JSON with priority, summary, actions, and parent_message.
    """
    # Build the prompt
    prompt = f"""You are an expert academic counselor for JEE aspirants. 

Student: {student_name}
Risk Score: {risk_score}/100
Risk Level: {risk_level}

Risk Factors:
{json.dumps(risk_factors, indent=2)}

Generate a personalized intervention plan in JSON format with this exact structure:
{{
  "priority": "high" or "medium" or "low",
  "summary": "2-3 sentence summary of the intervention plan",
  "actions": [
    {{
      "type": "counseling" or "academic" or "wellness",
      "title": "Short actionable title",
      "description": "Detailed description of what needs to be done",
      "timeline": "This week" or "Next 2 weeks" or "Ongoing"
    }}
  ],
  "parent_message": "Draft message to parent about the intervention plan"
}}

Guidelines:
- For high risk: Include immediate counseling, academic support, and wellness actions
- For medium risk: Focus on academic improvement and stress management
- For low risk: Focus on maintaining momentum and preventing burnout
- Be specific and actionable
- Parent message should be supportive, not alarming
- Return ONLY valid JSON, no additional text"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama returned status {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI service unavailable. Please ensure Ollama is running.",
                )
            
            result = response.json()
            ai_response = result.get("response", "{}")
            
            # Parse the JSON response
            try:
                intervention_data = json.loads(ai_response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI response: {ai_response}")
                # Fallback to default intervention
                intervention_data = {
                    "priority": "medium",
                    "summary": "Personalized intervention plan based on risk assessment",
                    "actions": [
                        {
                            "type": "counseling",
                            "title": "Schedule counseling session",
                            "description": "Meet with assigned faculty to discuss challenges and set goals",
                            "timeline": "This week",
                        },
                        {
                            "type": "academic",
                            "title": "Focus on weak subjects",
                            "description": "Dedicate extra time to subjects with lower scores",
                            "timeline": "Next 2 weeks",
                        },
                        {
                            "type": "wellness",
                            "title": "Improve sleep schedule",
                            "description": "Aim for 7-8 hours of sleep per night",
                            "timeline": "Ongoing",
                        },
                    ],
                    "parent_message": f"We have identified some areas where {student_name} could benefit from additional support. Our counseling team will work with them to create a personalized improvement plan.",
                }
            
            return intervention_data
            
    except httpx.ConnectError:
        logger.error("Failed to connect to Ollama")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service unavailable. Please ensure Ollama is running on localhost:11434.",
        )
    except Exception as e:
        logger.error(f"Error generating AI intervention: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate intervention: {str(e)}",
        )


# ── POST /api/students/{id}/interventions/generate ─────────────────────────────

@router.post(
    "/students/{student_id}/generate",
    response_model=GenerateInterventionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI intervention plan for a student",
)
async def generate_intervention(
    student_id: int,
    request: GenerateInterventionRequest,
    current_user: User = Depends(get_faculty_or_admin),
    db: Session = Depends(get_db),
) -> GenerateInterventionResponse:
    """
    Generate an AI-powered intervention plan using Ollama (llama3).
    
    The plan includes:
    - Priority level (high/medium/low)
    - Summary of the intervention
    - Action items with type, title, description, and timeline
    - Draft message to parents
    
    The intervention is saved to the database for tracking.
    """
    # Validate student exists
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student id={student_id} not found.",
        )
    
    # Check faculty assignment
    if (
        current_user.role == "faculty"
        and student.assigned_faculty_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this student.",
        )
    
    # Generate AI intervention
    ai_data = await generate_ai_intervention(
        student_name=student.full_name,
        risk_factors=request.risk_factors,
        risk_score=request.risk_score,
        risk_level=request.risk_level,
    )
    
    # Save to database
    intervention = Intervention(
        student_id=student_id,
        created_by=current_user.id,
        priority=ai_data["priority"],
        summary=ai_data["summary"],
        actions=ai_data["actions"],
        parent_message=ai_data["parent_message"],
        status="pending",
    )
    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    
    logger.info(
        f"Generated intervention for student_id={student_id} "
        f"by user_id={current_user.id} priority={ai_data['priority']}"
    )
    
    return GenerateInterventionResponse(
        id=intervention.id,
        student_id=intervention.student_id,
        priority=intervention.priority,
        summary=intervention.summary or "",
        actions=[ActionItem(**action) for action in (intervention.actions or [])],
        parent_message=intervention.parent_message or "",
        status=intervention.status,
        created_at=intervention.created_at,
    )


# ── GET /api/students/{id}/interventions ───────────────────────────────────────

@router.get(
    "/students/{student_id}",
    response_model=InterventionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get intervention history for a student",
)
async def get_interventions(
    student_id: int,
    current_user: User = Depends(get_faculty_or_admin),
    db: Session = Depends(get_db),
) -> InterventionListResponse:
    """
    Fetch all interventions for a student, ordered by creation date (newest first).
    """
    # Validate student exists
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student id={student_id} not found.",
        )
    
    # Check faculty assignment
    if (
        current_user.role == "faculty"
        and student.assigned_faculty_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this student.",
        )
    
    # Fetch interventions
    interventions = (
        db.query(Intervention)
        .filter(Intervention.student_id == student_id)
        .order_by(Intervention.created_at.desc())
        .all()
    )
    
    return InterventionListResponse(
        interventions=[
            InterventionListItem(
                id=inv.id,
                student_id=inv.student_id,
                priority=inv.priority,
                summary=inv.summary or "",
                status=inv.status,
                created_at=inv.created_at,
                completed_at=inv.completed_at,
            )
            for inv in interventions
        ]
    )


# ── PATCH /api/interventions/{id}/complete ────────────────────────────────────

@router.patch(
    "/{intervention_id}/complete",
    response_model=CompleteActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark an intervention as complete",
)
async def complete_intervention(
    intervention_id: int,
    current_user: User = Depends(get_faculty_or_admin),
    db: Session = Depends(get_db),
) -> CompleteActionResponse:
    """
    Mark an intervention as complete and set the completed_at timestamp.
    """
    # Fetch intervention
    intervention = (
        db.query(Intervention)
        .filter(Intervention.id == intervention_id)
        .first()
    )
    
    if not intervention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intervention id={intervention_id} not found.",
        )
    
    # Check faculty assignment
    if (
        current_user.role == "faculty"
        and intervention.student.assigned_faculty_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this student.",
        )
    
    # Update status
    intervention.status = "completed"
    intervention.completed_at = datetime.now(timezone.utc)
    db.commit()
    
    logger.info(
        f"Marked intervention_id={intervention_id} as complete "
        f"by user_id={current_user.id}"
    )
    
    return CompleteActionResponse(
        success=True,
        message="Intervention marked as complete",
    )
