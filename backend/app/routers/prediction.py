"""
routers/prediction.py
─────────────────────
Prediction and SHAP explanation endpoints.

  POST /predict/{student_id}           — run full pipeline, save to DB
  GET  /predict/explain/{student_id}   — latest SHAP explanation from DB
  GET  /predict/shap-plot/{student_id} — base64 waterfall PNG from DB
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.middleware.auth import get_faculty_or_admin
from backend.app.ml.feature_builder import build_features_from_db
from backend.app.ml.risk_scorer import compute_risk_score
from backend.app.models.database import (
    Alert,
    RiskAssessment,
    ShapExplanation,
    Student,
    User,
)
from backend.app.schemas.prediction import (
    ExplanationResponse,
    FeatureImpact,
    PredictionResponse,
    RiskComponents,
    WaterfallPlotResponse,
    SimpleExplanationResponse,
    SimpleFactor,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict", tags=["Prediction"])


# ── Shared helper — get student or 404 ───────────────────────────────────────

def _student_or_404(student_id: int, db: Session) -> Student:
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student id={student_id} not found.",
        )
    return s


# ── Shared helper — get latest assessment or 404 ──────────────────────────────

def _latest_assessment_or_404(student_id: int, db: Session) -> RiskAssessment:
    assessment = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.student_id == student_id)
        .order_by(RiskAssessment.assessed_at.desc())
        .first()
    )
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No risk assessment found for student id={student_id}. "
                   f"Run POST /predict/{student_id} first.",
        )
    return assessment


# ── POST /predict/{student_id} ────────────────────────────────────────────────

@router.post(
    "/{student_id}",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Run full dropout prediction pipeline for one student",
)
async def predict_student(
    student_id:   int,
    request:      Request,
    current_user: User    = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> PredictionResponse:
    """
    End-to-end prediction pipeline:

    1. Build 17 features from the database (mock tests, surveys, attendance)
    2. Run ensemble ML prediction (XGBoost × 0.55 + RF × 0.35 + LR × 0.10)
    3. Compute composite 0-100 risk score
    4. Generate real SHAP explanations
    5. Persist RiskAssessment + ShapExplanation to the database
    6. Create an Alert if risk level >= Medium
    7. Log prediction to prediction_logs table
    8. Return the full PredictionResponse

    Faculty can only predict for their assigned students.
    """
    try:
        # ── Retrieve ML components from app state ────────────────────────────────
        predictor = getattr(request.app.state, "predictor", None)
        explainer = getattr(request.app.state, "explainer", None)

        if predictor is None or explainer is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML models are not loaded. The service may be starting up.",
            )

        # ── Validate student + RBAC ──────────────────────────────────────────────
        student = _student_or_404(student_id, db)

        if (
            current_user.role == "faculty"
            and student.assigned_faculty_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this student.",
            )

        # ── Step 1: Build features ───────────────────────────────────────────────
        features_df = build_features_from_db(student_id, db)
        if features_df is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Could not build features: student data is missing or corrupt.",
            )

        features_dict = features_df.iloc[0].to_dict()

        # ── Step 2: ML prediction ────────────────────────────────────────────────
        pred = predictor.predict_single(features_dict)

        # ── Step 3: Risk score ───────────────────────────────────────────────────
        risk = compute_risk_score(
            ml_probability    = pred["ensemble_probability"],
            burnout_score     = features_dict["burnout_score"],
            mock_score_trend  = features_dict["mock_score_trend"],
            attendance_rate   = features_dict["attendance_rate"],
            sleep_hours       = features_dict["sleep_hours_avg"],
            parental_pressure = features_dict["parental_pressure_level"],
        )

        # ── Step 4: SHAP explanation ─────────────────────────────────────────────
        explanation    = explainer.explain(features_df)
        summary_text   = explainer.generate_summary_text(
            explanation["top_factors"],
            student_name=student.full_name.split()[0],   # first name
        )

        # Generate waterfall plot (can be expensive; run only if needed)
        try:
            waterfall_b64 = explainer.generate_waterfall_plot(features_df)
        except Exception as exc:
            logger.warning("Waterfall plot generation failed: %s", exc)
            waterfall_b64 = None

        # ── Step 5: Persist to DB ────────────────────────────────────────────────
        assessment = RiskAssessment(
            student_id=student_id,
            assessed_at=datetime.now(timezone.utc),
            risk_score=risk["score"],
            risk_level=risk["level"],
            ml_probability=pred["ensemble_probability"],
            model_version=pred["model_version"],
            feature_snapshot=features_dict,
        )
        db.add(assessment)
        db.flush()  # get assessment.id without committing

        shap_row = ShapExplanation(
            assessment_id=assessment.id,
            base_value=explanation["base_value"],
            top_factors=explanation["top_factors"],
            waterfall_plot=waterfall_b64,
            summary_text=summary_text,
        )
        db.add(shap_row)

        # ── Step 6: Create alert if risk >= Medium ────────────────────────────────
        alert_created = False
        if risk["level"] in ("Medium", "High", "Critical"):
            alert_message = (
                f"Student '{student.full_name}' has been flagged as "
                f"{risk['level']} risk (score={risk['score']}/100). "
                f"{summary_text}"
            )
            alert = Alert(
                student_id=student_id,
                assessment_id=assessment.id,
                assigned_to=student.assigned_faculty_id,
                alert_type="risk_threshold",
                risk_level=risk["level"],
                message=alert_message,
            )
            db.add(alert)
            alert_created = True

        db.commit()

        # ── Step 7: Log prediction to prediction_logs table ─────────────────────
        try:
            from backend.app.models.database import PredictionLog
            
            prediction_log = PredictionLog(
                student_id=student_id,
                user_id=current_user.id,
                user_role=current_user.role,
                risk_score=risk["score"],
                risk_level=risk["level"],
                ml_probability=pred["ensemble_probability"],
                model_version=pred["model_version"],
                inference_time_ms=pred["inference_time_ms"],
                feature_snapshot=features_dict,
                timestamp=datetime.now(timezone.utc),
            )
            db.add(prediction_log)
            db.commit()
            logger.info(f"Prediction logged for student_id={student_id}")
        except Exception as exc:
            logger.error(f"Failed to log prediction: {exc}")
            # Don't fail the prediction if logging fails

        logger.info(
            "Prediction complete: student_id=%d  risk=%s (%.1f)  alert=%s",
            student_id, risk["level"], risk["score"], alert_created,
        )

        # ── Step 8: Build response ────────────────────────────────────────────────
        top_factors = [FeatureImpact(**f) for f in explanation["top_factors"]]
        components  = RiskComponents(**risk["components"])

        return PredictionResponse(
            student_id=student_id,
            assessment_id=assessment.id,
            risk_score=risk["score"],
            risk_level=risk["level"],
            risk_color=risk["color"],
            urgency=risk["urgency"],
            ml_probability=pred["ensemble_probability"],
            predicted_dropout=pred["predicted_dropout"],
            risk_components=components,
            top_risk_factors=top_factors,
            counselor_summary=summary_text,
            model_version=pred["model_version"],
            assessed_at=assessment.assessed_at,
            alert_created=alert_created,
            inference_time_ms=pred["inference_time_ms"],
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as exc:
        # Catch any other exceptions and return a structured error
        logger.error(f"Prediction failed for student_id={student_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(exc)}",
        )


# ── GET /predict/explain/{student_id} ────────────────────────────────────────

@router.get(
    "/explain/{student_id}",
    response_model=ExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the latest SHAP explanation for a student",
)
async def get_explanation(
    student_id:   int,
    current_user: User    = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> ExplanationResponse:
    """
    Return the SHAP feature impacts stored from the most recent prediction.
    Call ``POST /predict/{id}`` first if no assessment exists.
    """
    _student_or_404(student_id, db)
    assessment = _latest_assessment_or_404(student_id, db)

    shap_row = assessment.shap_explanation
    if shap_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SHAP explanation not available for this assessment.",
        )

    top_factors = [FeatureImpact(**f) for f in (shap_row.top_factors or [])]

    return ExplanationResponse(
        student_id=student_id,
        assessment_id=assessment.id,
        assessed_at=assessment.assessed_at,
        base_value=shap_row.base_value or 0.0,
        top_factors=top_factors,
        counselor_summary=shap_row.summary_text,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level,
    )


# ── GET /predict/shap-plot/{student_id} ───────────────────────────────────────

@router.get(
    "/shap-plot/{student_id}",
    response_model=WaterfallPlotResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the SHAP waterfall plot (base64 PNG) for a student",
)
async def get_shap_plot(
    student_id:   int,
    current_user: User    = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> WaterfallPlotResponse:
    """
    Return the pre-generated SHAP waterfall plot from the latest assessment.
    The base64 string can be embedded as:
    ``<img src="data:image/png;base64,{plot_base64}" />``
    """
    _student_or_404(student_id, db)
    assessment = _latest_assessment_or_404(student_id, db)

    shap_row = assessment.shap_explanation
    if not shap_row or not shap_row.waterfall_plot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waterfall plot not available. Re-run prediction to regenerate.",
        )

    return WaterfallPlotResponse(
        student_id=student_id,
        assessment_id=assessment.id,
        plot_base64=shap_row.waterfall_plot,
        assessed_at=assessment.assessed_at,
    )


# ── GET /api/students/{id}/explanation ─────────────────────────────────────────

@router.get(
    "/students/{student_id}/explanation",
    response_model=SimpleExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get simplified SHAP explanation for a student",
)
async def get_student_explanation(
    student_id:   int,
    current_user: User    = Depends(get_faculty_or_admin),
    db:           Session = Depends(get_db),
) -> SimpleExplanationResponse:
    """
    Return a simplified SHAP explanation with risk score and factors.
    
    Response format:
    {
      "risk_score": 0.82,
      "factors": [
        {"feature": "attendance", "impact": +32, "value": "54%", "direction": "risk"},
        {"feature": "stress_level", "impact": +21, "value": "8/10", "direction": "risk"},
        {"feature": "math_score", "impact": -12, "value": "71%", "direction": "protective"}
      ]
    }
    """
    _student_or_404(student_id, db)
    assessment = _latest_assessment_or_404(student_id, db)

    shap_row = assessment.shap_explanation
    if shap_row is None or not shap_row.top_factors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SHAP explanation not available for this assessment.",
        )

    # Convert to simplified format
    factors = []
    for factor in shap_row.top_factors:
        direction = "risk" if factor["direction"] == "increases_risk" else "protective"
        impact = round(abs(factor["shap_value"]) * 100, 1)
        
        # Format value based on feature
        feature_name = factor["feature"]
        actual_value = factor["actual_value"]
        
        if "rate" in feature_name or "score" in feature_name:
            value_str = f"{actual_value:.0f}%"
        elif "hours" in feature_name:
            value_str = f"{actual_value:.1f}h"
        else:
            value_str = str(actual_value)
        
        factors.append(SimpleFactor(
            feature=feature_name,
            impact=impact,
            value=value_str,
            direction=direction
        ))

    # Normalize risk_score to 0-1 range
    risk_score_normalized = assessment.risk_score / 100.0

    return SimpleExplanationResponse(
        risk_score=round(risk_score_normalized, 2),
        factors=factors
    )
