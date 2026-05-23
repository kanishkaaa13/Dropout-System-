"""
backend/app/middleware/audit.py
────────────────────────────────
Request audit logging middleware.

Every HTTP request is logged with:
  - user_id   (decoded from JWT Bearer if present, else 'anonymous')
  - method + path
  - HTTP status code
  - client IP
  - response time (ms)

Writes asynchronously to the AuditLog table so it never blocks the response.
Falls back to structured stderr logging if the DB write fails.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from fastapi import Request, Response
from jose   import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types           import ASGIApp

from backend.app.config import settings

log = logging.getLogger(__name__)


def _extract_user_id(request: Request) -> Optional[str]:
    """
    Attempt to decode the Bearer token and return the subject (user email).
    Returns None on any failure — audit should never crash the request.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[len("Bearer "):]
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},   # we only want the identity, not validity
        )
        return payload.get("sub")
    except (JWTError, Exception):
        return None


def _write_audit_log(
    user_id:     Optional[str],
    method:      str,
    path:        str,
    status_code: int,
    ip:          str,
    duration_ms: float,
) -> None:
    """
    Write one row to the AuditLog table.
    Runs in a background thread via run_in_executor — never propagated.
    """
    try:
        import json
        from backend.app.database       import SessionLocal
        from backend.app.models.database import AuditLog
        from datetime                   import datetime, timezone

        db = SessionLocal()
        try:
            entry = AuditLog(
                user_id     = None,           # FK to users.id — resolved async lookup not worth the cost
                action      = f"{method} {path}",
                ip_address  = ip,
                timestamp   = datetime.now(timezone.utc),
                details     = json.dumps({
                    "user":        user_id,   # email string from JWT sub
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                }),
            )
            db.add(entry)
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        log.error(
            "AuditLog DB write failed: user=%s %s %s → %d (%.1fms) | %s",
            user_id, method, path, status_code, duration_ms, exc,
        )



class AuditMiddleware(BaseHTTPMiddleware):
    """
    Starlette BaseHTTPMiddleware that intercepts every request/response
    and logs an audit record.
    """

    def __init__(self, app: ASGIApp, exclude_paths: Optional[list[str]] = None) -> None:
        super().__init__(app)
        # Paths to skip (health checks, metrics — high-volume, low-value)
        self._exclude: set[str] = set(exclude_paths or ["/health", "/metrics"])

    async def dispatch(
        self,
        request:  Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if request.url.path in self._exclude:
            return await call_next(request)

        start    = time.perf_counter()
        response = await call_next(request)
        elapsed  = (time.perf_counter() - start) * 1000   # → milliseconds

        user_id     = _extract_user_id(request)
        status_code = response.status_code
        method      = request.method
        path        = request.url.path
        ip          = request.client.host if request.client else "unknown"

        # Structured log (always written — even if DB is down)
        log.info(
            "AUDIT | user=%-30s | %s %-50s | %d | %.1fms | ip=%s",
            user_id or "anonymous",
            method.ljust(6),
            path,
            status_code,
            elapsed,
            ip,
        )

        # Async DB write — fire and forget (don't await so response isn't delayed)
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_in_executor(
            None,
            _write_audit_log,
            user_id, method, path, status_code, ip, elapsed,
        )

        return response
