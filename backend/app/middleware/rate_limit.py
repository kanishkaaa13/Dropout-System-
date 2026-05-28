"""
middleware/rate_limit.py
────────────────────────
Simple rate limiting middleware for FastAPI.
Limits requests per time window to prevent abuse.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.
    Limits requests per IP address per time window.
    """

    def __init__(self, app, requests: int = 100, window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            requests: Number of requests allowed per window
            window: Time window in seconds
        """
        super().__init__(app)
        self.requests = requests
        self.window = window
        self.request_counts = defaultdict(list)
        self.enabled = settings.RATE_LIMIT_ENABLED

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.
        """
        if not self.enabled:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        if self._is_rate_limited(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "message": "Rate limit exceeded. Please try again later.",
                        "type": "rate_limit_error",
                        "status_code": 429,
                    }
                },
            )
        
        # Record request
        self._record_request(client_ip)
        
        # Process request
        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.
        """
        # Check for forwarded headers (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str) -> bool:
        """
        Check if client IP has exceeded rate limit.
        """
        now = time.time()
        
        # Clean old requests outside the window
        self.request_counts[client_ip] = [
            timestamp for timestamp in self.request_counts[client_ip]
            if now - timestamp < self.window
        ]
        
        # Check if limit exceeded
        return len(self.request_counts[client_ip]) >= self.requests

    def _record_request(self, client_ip: str) -> None:
        """
        Record a request for the client IP.
        """
        self.request_counts[client_ip].append(time.time())
