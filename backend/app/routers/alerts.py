"""
backend/app/routers/alerts.py
──────────────────────────────
Alert management endpoints.

Routes
──────
  GET  /alerts              — list (paginated, filterable)
  GET  /alerts/stats        — summary counts
  GET  /alerts/{id}         — single alert detail
  PUT  /alerts/{id}/resolve — mark resolved + optional note
  PUT  /alerts/{id}/read    — mark as read
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database            import get_db
from backend.app.middleware.auth     import get_current_user, get_faculty_or_admin
from backend.app.models.database     import Alert, User
from backend.app.services.alert_service import (
    get_alerts,
    resolve_alert,
    mark_alert_read,
    get_unresolved_count,
    get_alert_stats,
)

log    = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["Alerts"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class AlertOut(BaseModel):
    id:              int
    student_id:      int
    assessment_id:   Optional[int]
    assigned_to:     Optional[int]
    alert_type:      str
    risk_level:      str
    message:         str
    is_resolved:     bool
    is_read:         bool
    resolution_note: Optional[str]
    created_at:      Optional[str]

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_obj(cls, a: Alert) -> "AlertOut":
        return cls(
            id              = a.id,
            student_id      = a.student_id,
            assessment_id   = a.assessment_id,
            assigned_to     = a.assigned_to,
            alert_type      = a.alert_type,
            risk_level      = a.risk_level,
            message         = a.message,
            is_resolved     = a.is_resolved,
            is_read         = a.is_read,
            resolution_note = getattr(a, "resolution_note", None),
            created_at      = a.created_at.isoformat() if a.created_at else None,
        )


class AlertStatsOut(BaseModel):
    total:      int
    unresolved: int
    by_level:   dict[str, int]


class ResolveRequest(BaseModel):
    note: Optional[str] = None


class AlertListOut(BaseModel):
    items: list[AlertOut]
    total: int
    page:  int
    size:  int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=AlertStatsOut, summary="Alert queue statistics")
def alert_stats(
    current_user: User    = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> AlertStatsOut:
    stats = get_alert_stats(current_user.id, current_user.role, db)
    return AlertStatsOut(**stats)


@router.get("", response_model=AlertListOut, summary="List alerts (paginated)")
def list_alerts(
    page:        int            = Query(1, ge=1),
    size:        int            = Query(20, ge=1, le=100),
    is_resolved: Optional[bool] = Query(None),
    risk_level:  Optional[str]  = Query(None),
    current_user: User    = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> AlertListOut:
    skip   = (page - 1) * size
    alerts = get_alerts(
        user_id=current_user.id,
        role=current_user.role,
        db=db,
        skip=skip,
        limit=size,
        is_resolved=is_resolved,
        risk_level=risk_level,
    )
    # Count total (without pagination)
    total_alerts = get_alerts(
        user_id=current_user.id,
        role=current_user.role,
        db=db,
        skip=0,
        limit=100_000,
        is_resolved=is_resolved,
        risk_level=risk_level,
    )
    return AlertListOut(
        items=[AlertOut.from_orm_obj(a) for a in alerts],
        total=len(total_alerts),
        page=page,
        size=size,
    )


@router.get("/{alert_id}", response_model=AlertOut, summary="Get single alert")
def get_alert(
    alert_id:     int,
    current_user: User    = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> AlertOut:
    alert: Optional[Alert] = db.query(Alert).filter_by(id=alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    # Faculty can only view their own alerts
    if current_user.role == "faculty" and alert.assigned_to != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorised to view this alert")

    return AlertOut.from_orm_obj(alert)


@router.put("/{alert_id}/resolve", response_model=AlertOut, summary="Resolve an alert")
def resolve(
    alert_id:     int,
    body:         ResolveRequest,
    current_user: User    = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> AlertOut:
    updated = resolve_alert(
        alert_id=alert_id,
        user_id=current_user.id,
        role=current_user.role,
        note=body.note,
        db=db,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found or you are not authorised to resolve it",
        )
    db.commit()
    return AlertOut.from_orm_obj(updated)


@router.put("/{alert_id}/read", response_model=AlertOut, summary="Mark alert as read")
def mark_read(
    alert_id:     int,
    current_user: User    = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> AlertOut:
    updated = mark_alert_read(
        alert_id=alert_id,
        user_id=current_user.id,
        role=current_user.role,
        db=db,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found or not authorised",
        )
    db.commit()
    return AlertOut.from_orm_obj(updated)
