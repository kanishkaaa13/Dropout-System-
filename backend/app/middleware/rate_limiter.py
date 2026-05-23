"""
backend/app/middleware/rate_limiter.py
───────────────────────────────────────
SlowAPI-based rate limiting middleware.

Limits
──────
  /api/v1/auth/login   →  5  req/min  (brute-force protection)
  all other endpoints  → 100 req/min  (general API protection)

All 429 responses are JSON (not HTML).
"""

from __future__ import annotations

import logging

from fastapi           import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi           import Limiter, _rate_limit_exceeded_handler
from slowapi.errors    import RateLimitExceeded
from slowapi.util      import get_remote_address

log = logging.getLogger(__name__)

# ── Limiter instance (keyed by client IP) ─────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


async def _json_rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """
    Override the default HTML 429 response with a JSON body.
    This ensures API clients always receive machine-readable errors.
    """
    log.warning(
        "Rate limit exceeded: ip=%s path=%s limit=%s",
        get_remote_address(request),
        request.url.path,
        exc.detail,
    )
    return JSONResponse(
        status_code=429,
        content={
            "detail":     "Too many requests. Please slow down.",
            "limit":      str(exc.detail),
            "path":       str(request.url.path),
            "retry_after": "60 seconds",
        },
        headers={"Retry-After": "60"},
    )


def setup_rate_limiter(app: FastAPI) -> None:
    """
    Register the SlowAPI limiter and its exception handler on the FastAPI app.
    Call this once inside create_app().

    Example
    -------
        from backend.app.middleware.rate_limiter import limiter, setup_rate_limiter
        setup_rate_limiter(app)
        app.state.limiter = limiter
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _json_rate_limit_exceeded_handler)
    log.info("Rate limiter configured — default: 100/min, login: 5/min")
