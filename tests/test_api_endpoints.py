"""
test_api_endpoints.py
---------------------
Integration tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class TestHealthEndpoint:
    """Test the /health endpoint."""

    def test_health_endpoint_response(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_structure(self, client):
        """Test that health endpoint returns correct structure."""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "version" in data
        assert "environment" in data
        assert "uptime_seconds" in data
        assert "uptime_hours" in data
        assert "ml_models_loaded" in data
        assert "model_info" in data

    def test_health_endpoint_uptime(self, client):
        """Test that uptime is positive."""
        response = client.get("/health")
        data = response.json()
        
        assert data["uptime_seconds"] >= 0
        assert data["uptime_hours"] >= 0

    def test_health_endpoint_model_info(self, client):
        """Test that model info is included when models are loaded."""
        response = client.get("/health")
        data = response.json()
        
        if data["ml_models_loaded"]:
            model_info = data["model_info"]
            assert "model_version" in model_info
            assert "pipeline" in model_info
            assert "n_features" in model_info


class TestPredictionEndpoints:
    """Test prediction-related endpoints."""

    def test_predict_endpoint_requires_auth(self, client):
        """Test that prediction endpoint requires authentication."""
        response = client.post("/api/v1/predict/1")
        assert response.status_code == 401

    def test_explain_endpoint_requires_auth(self, client):
        """Test that explain endpoint requires authentication."""
        response = client.get("/api/v1/predict/explain/1")
        assert response.status_code == 401

    def test_shap_plot_endpoint_requires_auth(self, client):
        """Test that SHAP plot endpoint requires authentication."""
        response = client.get("/api/v1/predict/shap-plot/1")
        assert response.status_code == 401

    def test_predict_endpoint_with_auth(self, client, auth_headers):
        """Test that prediction endpoint works with authentication."""
        # This test assumes a student with ID 1 exists
        response = client.post(
            "/api/v1/predict/1",
            headers=auth_headers
        )
        # May return 404 if student doesn't exist, but should not be 401
        assert response.status_code != 401

    def test_predict_endpoint_invalid_student(self, client, auth_headers):
        """Test that prediction endpoint returns 404 for non-existent student."""
        response = client.post(
            "/api/v1/predict/99999",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_endpoint(self, client):
        """Test that login endpoint exists."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword"
            }
        )
        # May return 401 for invalid credentials, but should not be 404
        assert response.status_code != 404

    def test_login_endpoint_validation(self, client):
        """Test that login endpoint validates input."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "invalid-email",
                "password": "short"
            }
        )
        # Should return validation error (422)
        assert response.status_code == 422

    def test_logout_endpoint_requires_auth(self, client):
        """Test that logout endpoint requires authentication."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401


class TestStudentEndpoints:
    """Test student-related endpoints."""

    def test_students_endpoint_requires_auth(self, client):
        """Test that students endpoint requires authentication."""
        response = client.get("/api/v1/students")
        assert response.status_code == 401

    def test_students_endpoint_with_auth(self, client, auth_headers):
        """Test that students endpoint works with authentication."""
        response = client.get("/api/v1/students", headers=auth_headers)
        # Should not be 401
        assert response.status_code != 401

    def test_student_detail_endpoint_requires_auth(self, client):
        """Test that student detail endpoint requires authentication."""
        response = client.get("/api/v1/students/1")
        assert response.status_code == 401

    def test_student_detail_endpoint_with_auth(self, client, auth_headers):
        """Test that student detail endpoint works with authentication."""
        response = client.get("/api/v1/students/1", headers=auth_headers)
        # May return 404 if student doesn't exist, but should not be 401
        assert response.status_code != 401


class TestErrorHandling:
    """Test error handling across endpoints."""

    def test_404_error_response(self, client):
        """Test that 404 errors return proper error format."""
        response = client.get("/api/v1/nonexistent-endpoint")
        assert response.status_code == 404

    def test_405_method_not_allowed(self, client):
        """Test that wrong HTTP methods return 405."""
        response = client.get("/api/v1/auth/login")
        assert response.status_code == 405

    def test_malformed_json(self, client):
        """Test that malformed JSON returns 422."""
        response = client.post(
            "/api/v1/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


class TestCORS:
    """Test CORS configuration."""

    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = client.options("/health")
        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers or \
               "Access-Control-Allow-Origin" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
