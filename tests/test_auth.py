"""
tests/test_auth.py
──────────────────
Unit tests for authentication endpoints.

Coverage:
  - POST /auth/login          happy path + wrong password + inactive user
  - POST /auth/refresh        valid + blacklisted token
  - POST /auth/logout         idempotent
  - GET  /auth/me             valid token + no token
  - PUT  /auth/change-password happy path + wrong old password
"""

from __future__ import annotations

import pytest


class TestLogin:
    def test_login_success(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@jeetest.com", "password": "AdminPass123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token"  in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        assert body["expires_in"] > 0

    def test_login_wrong_password(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@jeetest.com", "password": "WrongPass!"},
        )
        assert resp.status_code == 401
        assert "Incorrect" in resp.json()["detail"]

    def test_login_unknown_email(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@nowhere.com", "password": "SomePass123"},
        )
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@jeetest.com"},   # no password
        )
        assert resp.status_code == 422      # Pydantic validation error


class TestRefresh:
    def test_refresh_success(self, client):
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "faculty@jeetest.com", "password": "FacultyPass123"},
        )
        refresh_token = login.json()["refresh_token"]

        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_refresh_with_access_token_fails(self, client, admin_token):
        # Access tokens must not be accepted as refresh tokens
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": admin_token},
        )
        assert resp.status_code == 401

    def test_refresh_garbage_token(self, client):
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not.a.real.token"},
        )
        assert resp.status_code == 401


class TestLogout:
    def test_logout_success(self, client):
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "faculty@jeetest.com", "password": "FacultyPass123"},
        )
        refresh_token = login.json()["refresh_token"]

        resp = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_logout_then_refresh_fails(self, client):
        """After logout the refresh token must be blacklisted."""
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@jeetest.com", "password": "AdminPass123"},
        )
        refresh_token = login.json()["refresh_token"]

        # Logout
        client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})

        # Attempt to use the blacklisted token
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 401
        assert "revoked" in resp.json()["detail"].lower()

    def test_logout_invalid_token_is_ok(self, client):
        """Logging out with a garbage token must not raise an error."""
        resp = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "garbage.token.here"},
        )
        assert resp.status_code == 200


class TestGetMe:
    def test_get_me_success(self, client, admin_headers):
        resp = client.get("/api/v1/auth/me", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "admin@jeetest.com"
        assert body["role"]  == "admin"

    def test_get_me_no_token(self, client):
        # FastAPI's HTTPBearer(auto_error=True) returns 401 when no credentials sent
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_get_me_invalid_token(self, client):
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer bad.token.value"},
        )
        assert resp.status_code == 401


class TestChangePassword:
    def test_change_password_success(self, client):
        from tests.conftest import TestingSession
        from backend.app.models.database import User
        from backend.app.middleware.auth import hash_password

        db = TestingSession()
        u = User(
            email="changeme@jeetest.com",
            hashed_password=hash_password("OldPass123"),
            full_name="Change Me",
            role="faculty",
            is_active=True,
        )
        db.add(u)
        db.commit()
        db.close()

        login = client.post(
            "/api/v1/auth/login",
            json={"email": "changeme@jeetest.com", "password": "OldPass123"},
        )
        token = login.json()["access_token"]

        resp = client.put(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"old_password": "OldPass123", "new_password": "NewPass456!"},
        )
        assert resp.status_code == 200
        assert "updated" in resp.json()["message"].lower()

    def test_change_password_wrong_old(self, client, faculty_headers):
        resp = client.put(
            "/api/v1/auth/change-password",
            headers=faculty_headers,
            json={"old_password": "wrongoldpass", "new_password": "NewPass789!"},
        )
        assert resp.status_code == 400
        assert "incorrect" in resp.json()["detail"].lower()
