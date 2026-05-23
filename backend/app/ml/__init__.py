"""
backend.app.ml
──────────────
JEE Dropout Prediction — ML sub-package.

Exports
-------
JEEDropoutPredictor  — loads models, runs predictions
SHAPExplainer        — SHAP explanations + waterfall plots
compute_risk_score   — composite 0-100 risk scorer
build_features_from_db, compute_mock_score_trend, compute_study_consistency
"""

from .predictor import JEEDropoutPredictor
from .explainer import SHAPExplainer
from .risk_scorer import compute_risk_score
from .feature_builder import (
    build_features_from_db,
    compute_mock_score_trend,
    compute_study_consistency,
)

__all__ = [
    "JEEDropoutPredictor",
    "SHAPExplainer",
    "compute_risk_score",
    "build_features_from_db",
    "compute_mock_score_trend",
    "compute_study_consistency",
]
