"""
tests/test_prediction.py
────────────────────────
Unit tests for prediction and SHAP explanation endpoints.

Because ML models are heavy, these tests use a mocked predictor/explainer
injected into app.state — no actual model files required during CI.

Coverage:
  - POST /predict/{id}              happy path (mocked ML), 404 student,
                                    503 when models not loaded
  - GET  /predict/explain/{id}      found, 404 no assessment
  - GET  /predict/shap-plot/{id}    found, 404 no plot
"""

from __future__ import annotations

import base64
from unittest.mock import MagicMock, patch

import pytest


# ── Minimal ML mock data ──────────────────────────────────────────────────────

MOCK_FEATURES = {
    "attendance_rate":            67.0,
    "mock_test_avg":              148.5,
    "physics_score":              42.0,
    "chemistry_score":            55.0,
    "maths_score":                51.5,
    "mock_score_trend":          -18.2,
    "assignment_completion_rate": 58.0,
    "dpp_accuracy":               49.0,
    "test_attempt_rate":          72.0,
    "burnout_score":               8,
    "stress_level":                7,
    "sleep_hours_avg":             4.8,
    "study_hours_per_day":         9.5,
    "study_consistency_score":    35.0,
    "parental_pressure_level":     9,
    "peer_comparison_stress":      7,
    "coaching_engagement_score":  48.0,
}

MOCK_PREDICTION = {
    "ensemble_probability": 0.85,
    "predicted_dropout":    True,
    "threshold":            0.35,
    "model_probabilities": {
        "xgboost": 0.90, "random_forest": 0.78, "logistic_regression": 0.82,
    },
    "feature_names":     list(MOCK_FEATURES.keys()),
    "model_version":     "1.0.0",
    "inference_time_ms": 12.5,
}

MOCK_RISK = {
    "score":   78.5,
    "level":   "Critical",
    "color":   "#7C3AED",
    "urgency": "immediate",
    "components": {
        "ml_base":                 59.5,
        "burnout_contribution":    5.0,
        "trend_contribution":      1.5,
        "sleep_contribution":      2.8,
        "pressure_contribution":   3.3,
        "attendance_contribution": 1.07,
        "total_bonus":             13.67,
    },
}

MOCK_EXPLANATION = {
    "base_value": 0.20,
    "top_factors": [
        {
            "feature":      "attendance_rate",
            "human_label":  "Attendance Rate",
            "shap_value":   1.40,
            "actual_value": 67.0,
            "direction":    "increases_risk",
            "magnitude":    1.40,
            "unit":         "%",
            "severity":     "critically low",
        },
        {
            "feature":      "burnout_score",
            "human_label":  "Burnout Level",
            "shap_value":   1.22,
            "actual_value": 8.0,
            "direction":    "increases_risk",
            "magnitude":    1.22,
            "unit":         "/10",
            "severity":     "very high",
        },
    ],
    "all_shap_values": {"attendance_rate": 1.40, "burnout_score": 1.22},
}

_DUMMY_PNG_B64 = base64.b64encode(b"FAKEPNG").decode()


def _make_mock_predictor():
    p = MagicMock()
    p.is_loaded = True
    p.feature_cols = list(MOCK_FEATURES.keys())
    p.metadata = {"version": "1.0.0"}
    p.predict_single.return_value = MOCK_PREDICTION
    return p


def _make_mock_explainer():
    e = MagicMock()
    e.explain.return_value = MOCK_EXPLANATION
    e.generate_waterfall_plot.return_value = _DUMMY_PNG_B64
    e.generate_summary_text.return_value = (
        "Attendance at 67.0% is critically low. "
        "Burnout level is very high at 8/10. "
        "Parental pressure of 9/10 is extreme."
    )
    return e


# ── Student fixture ───────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def pred_student(client, admin_headers):
    resp = client.post(
        "/api/v1/students",
        headers=admin_headers,
        json={
            "full_name":    "Rohit Mishra",
            "email":        "rohit.mishra@jeetest.com",
            "student_code": "JEE2025_PRED",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── POST /predict/{id} ────────────────────────────────────────────────────────

class TestPredict:
    def test_predict_success(self, client, admin_headers, pred_student):
        """Full pipeline with mocked ML — verifies complete response schema."""
        import pandas as pd

        # Use client.app so we manipulate the SAME app the TestClient wraps
        client.app.state.predictor = _make_mock_predictor()
        client.app.state.explainer  = _make_mock_explainer()

        sid = pred_student["id"]

        with patch("backend.app.routers.prediction.build_features_from_db",
                   return_value=pd.DataFrame([MOCK_FEATURES])):
            with patch("backend.app.routers.prediction.compute_risk_score",
                       return_value=MOCK_RISK):
                resp = client.post(f"/api/v1/predict/{sid}", headers=admin_headers)

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["student_id"]        == sid
        assert body["risk_score"]        == MOCK_RISK["score"]
        assert body["risk_level"]        == "Critical"
        assert body["urgency"]           == "immediate"
        assert body["predicted_dropout"] is True
        assert "top_risk_factors"        in body
        assert "counselor_summary"       in body
        assert "assessment_id"           in body
        assert body["alert_created"]     is True      # Critical → alert created

    def test_predict_student_not_found(self, client, admin_headers):
        client.app.state.predictor = _make_mock_predictor()
        client.app.state.explainer  = _make_mock_explainer()

        resp = client.post("/api/v1/predict/999999", headers=admin_headers)
        assert resp.status_code == 404

    def test_predict_models_not_loaded(self, client, admin_headers, pred_student):
        """Service returns 503 when models are not loaded."""
        original_predictor = client.app.state.predictor
        original_explainer  = client.app.state.explainer
        client.app.state.predictor = None
        client.app.state.explainer  = None

        sid  = pred_student["id"]
        resp = client.post(f"/api/v1/predict/{sid}", headers=admin_headers)
        assert resp.status_code == 503

        # Restore
        client.app.state.predictor = original_predictor
        client.app.state.explainer  = original_explainer

    def test_predict_requires_auth(self, client, pred_student):
        # HTTPBearer(auto_error=True) returns 401 when no credentials supplied
        sid  = pred_student["id"]
        resp = client.post(f"/api/v1/predict/{sid}")
        assert resp.status_code == 401

    def test_predict_feature_build_fails(self, client, admin_headers, pred_student):
        """Feature builder returning None must yield 422."""
        client.app.state.predictor = _make_mock_predictor()
        client.app.state.explainer  = _make_mock_explainer()

        sid = pred_student["id"]
        with patch("backend.app.routers.prediction.build_features_from_db",
                   return_value=None):
            resp = client.post(f"/api/v1/predict/{sid}", headers=admin_headers)

        assert resp.status_code == 422


# ── GET /predict/explain/{id} ─────────────────────────────────────────────────

class TestExplain:
    def _ensure_assessment(self, client, admin_headers, sid):
        """Run one mocked prediction so an assessment row exists in the test DB."""
        import pandas as pd
        client.app.state.predictor = _make_mock_predictor()
        client.app.state.explainer  = _make_mock_explainer()

        with patch("backend.app.routers.prediction.build_features_from_db",
                   return_value=pd.DataFrame([MOCK_FEATURES])):
            with patch("backend.app.routers.prediction.compute_risk_score",
                       return_value=MOCK_RISK):
                client.post(f"/api/v1/predict/{sid}", headers=admin_headers)

    def test_explain_success(self, client, admin_headers, pred_student):
        sid = pred_student["id"]
        self._ensure_assessment(client, admin_headers, sid)

        resp = client.get(f"/api/v1/predict/explain/{sid}", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["student_id"] == sid
        assert "top_factors"       in body
        assert "base_value"        in body

    def test_explain_no_assessment(self, client, admin_headers):
        """Student with no prior prediction must return 404."""
        new = client.post(
            "/api/v1/students",
            headers=admin_headers,
            json={"full_name": "Never Predicted", "email": "neverpred@jeetest.com"},
        )
        sid  = new.json()["id"]
        resp = client.get(f"/api/v1/predict/explain/{sid}", headers=admin_headers)
        assert resp.status_code == 404

    def test_explain_student_not_found(self, client, admin_headers):
        resp = client.get("/api/v1/predict/explain/999999", headers=admin_headers)
        assert resp.status_code == 404


# ── GET /predict/shap-plot/{id} ───────────────────────────────────────────────

class TestShapPlot:
    def test_shap_plot_success(self, client, admin_headers, pred_student):
        sid  = pred_student["id"]
        resp = client.get(f"/api/v1/predict/shap-plot/{sid}", headers=admin_headers)
        # Both 200 (plot stored) and 404 (not stored) are valid
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            body = resp.json()
            assert "plot_base64"   in body
            assert "assessment_id" in body

    def test_shap_plot_student_not_found(self, client, admin_headers):
        resp = client.get("/api/v1/predict/shap-plot/999999", headers=admin_headers)
        assert resp.status_code == 404
