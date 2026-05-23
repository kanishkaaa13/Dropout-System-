"""
tests/test_students.py
──────────────────────
Unit tests for student management endpoints.

Coverage:
  - GET  /students              pagination, search, RBAC
  - POST /students              admin create, faculty forbidden
  - GET  /students/{id}         found, 404, RBAC
  - PUT  /students/{id}         admin update, faculty forbidden
  - POST /students/{id}/mock-tests   create, validate scores
  - GET  /students/{id}/mock-tests   list
  - POST /students/{id}/surveys      create
  - GET  /students/{id}/risk-history empty list
"""

from __future__ import annotations

import pytest


# ── Shared student fixture ─────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def created_student(client, admin_headers):
    resp = client.post(
        "/api/v1/students",
        headers=admin_headers,
        json={
            "full_name":      "Arjun Sharma",
            "email":          "arjun.sharma@jeetest.com",
            "student_code":   "JEE2025_001",
            "target_rank":    500,
            "target_college": "IIT Bombay",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestListStudents:
    def test_admin_can_list(self, client, admin_headers):
        resp = client.get("/api/v1/students", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert body["page"] == 1

    def test_faculty_can_list(self, client, faculty_headers):
        resp = client.get("/api/v1/students", headers=faculty_headers)
        assert resp.status_code == 200

    def test_unauthenticated_rejected(self, client):
        # HTTPBearer(auto_error=True) returns 401 when no credentials are provided
        resp = client.get("/api/v1/students")
        assert resp.status_code == 401

    def test_pagination_params(self, client, admin_headers):
        resp = client.get(
            "/api/v1/students",
            headers=admin_headers,
            params={"page": 1, "size": 5},
        )
        assert resp.status_code == 200
        assert resp.json()["size"] == 5

    def test_search_filter(self, client, admin_headers, created_student):
        resp = client.get(
            "/api/v1/students",
            headers=admin_headers,
            params={"search": "Arjun"},
        )
        assert resp.status_code == 200
        names = [s["full_name"] for s in resp.json()["items"]]
        assert "Arjun Sharma" in names

    def test_risk_level_filter(self, client, admin_headers):
        # No assessments yet — result is empty but status must be 200
        resp = client.get(
            "/api/v1/students",
            headers=admin_headers,
            params={"risk_level": "Low"},
        )
        assert resp.status_code == 200


class TestCreateStudent:
    def test_admin_creates_student(self, client, admin_headers):
        resp = client.post(
            "/api/v1/students",
            headers=admin_headers,
            json={"full_name": "Priya Verma", "email": "priya.verma@jeetest.com"},
        )
        assert resp.status_code == 201
        assert resp.json()["full_name"] == "Priya Verma"

    def test_faculty_cannot_create(self, client, faculty_headers):
        resp = client.post(
            "/api/v1/students",
            headers=faculty_headers,
            json={"full_name": "Blocked Student"},
        )
        assert resp.status_code == 403

    def test_duplicate_email_rejected(self, client, admin_headers, created_student):
        resp = client.post(
            "/api/v1/students",
            headers=admin_headers,
            json={
                "full_name": "Duplicate",
                "email": created_student["email"],   # already exists
            },
        )
        assert resp.status_code == 409

    def test_missing_full_name_rejected(self, client, admin_headers):
        resp = client.post(
            "/api/v1/students",
            headers=admin_headers,
            json={"email": "nofullname@jeetest.com"},
        )
        assert resp.status_code == 422


class TestGetStudent:
    def test_get_existing_student(self, client, admin_headers, created_student):
        sid  = created_student["id"]
        resp = client.get(f"/api/v1/students/{sid}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == sid

    def test_get_nonexistent_student(self, client, admin_headers):
        resp = client.get("/api/v1/students/999999", headers=admin_headers)
        assert resp.status_code == 404

    def test_faculty_cannot_view_unassigned(self, client, faculty_headers, created_student):
        # Student has no assigned_faculty_id → faculty sees 403
        sid  = created_student["id"]
        resp = client.get(f"/api/v1/students/{sid}", headers=faculty_headers)
        assert resp.status_code == 403


class TestUpdateStudent:
    def test_admin_updates_student(self, client, admin_headers, created_student):
        sid  = created_student["id"]
        resp = client.put(
            f"/api/v1/students/{sid}",
            headers=admin_headers,
            json={"target_rank": 100, "target_college": "IIT Delhi"},
        )
        assert resp.status_code == 200
        assert resp.json()["target_rank"] == 100

    def test_faculty_cannot_update(self, client, faculty_headers, created_student):
        sid  = created_student["id"]
        resp = client.put(
            f"/api/v1/students/{sid}",
            headers=faculty_headers,
            json={"target_rank": 999},
        )
        assert resp.status_code == 403


class TestMockTests:
    def test_add_mock_test(self, client, admin_headers, created_student):
        sid  = created_student["id"]
        resp = client.post(
            f"/api/v1/students/{sid}/mock-tests",
            headers=admin_headers,
            json={
                "test_date":       "2025-09-01T10:00:00",
                "test_name":       "Minor Test 1",
                "test_type":       "minor",
                "total_score":     210.0,
                "physics_score":   72.0,
                "chemistry_score": 68.0,
                "maths_score":     70.0,
                "percentile":      78.5,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["total_score"] == 210.0

    def test_score_out_of_range_rejected(self, client, admin_headers, created_student):
        sid  = created_student["id"]
        resp = client.post(
            f"/api/v1/students/{sid}/mock-tests",
            headers=admin_headers,
            json={
                "test_date":   "2025-09-10T10:00:00",
                "total_score": 999.0,     # > 360 — must be rejected
            },
        )
        assert resp.status_code == 422

    def test_list_mock_tests(self, client, admin_headers, created_student):
        sid  = created_student["id"]
        resp = client.get(f"/api/v1/students/{sid}/mock-tests", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1


class TestSurveys:
    def test_submit_survey(self, client, admin_headers, created_student):
        sid  = created_student["id"]
        resp = client.post(
            f"/api/v1/students/{sid}/surveys",
            headers=admin_headers,
            json={
                "burnout_score":          7,
                "stress_level":           6,
                "sleep_hours_avg":        5.5,
                "study_hours_per_day":    9.0,
                "parental_pressure":      8,
                "peer_comparison_stress": 6,
                "motivation_level":       4,
                "notes":                  "Feeling overwhelmed this week.",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["burnout_score"] == 7

    def test_survey_out_of_range(self, client, admin_headers, created_student):
        sid  = created_student["id"]
        resp = client.post(
            f"/api/v1/students/{sid}/surveys",
            headers=admin_headers,
            json={
                "burnout_score":          15,  # > 10 — must be rejected
                "stress_level":           6,
                "sleep_hours_avg":        6.0,
                "study_hours_per_day":    8.0,
                "parental_pressure":      5,
                "peer_comparison_stress": 4,
            },
        )
        assert resp.status_code == 422


class TestRiskHistory:
    def test_risk_history_empty(self, client, admin_headers, created_student):
        sid  = created_student["id"]
        resp = client.get(f"/api/v1/students/{sid}/risk-history", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)   # empty list is valid
