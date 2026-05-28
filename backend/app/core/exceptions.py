"""
core/exceptions.py
──────────────────
Global exception handlers for FastAPI.
Provides structured error responses without exposing stack traces.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTPException with structured error response.
    """
    error_id = str(uuid.uuid4())
    
    logger.warning(
        f"HTTPException: {exc.status_code} - {exc.detail} - Path: {request.url.path} - Error ID: {error_id}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": "http_error",
                "status_code": exc.status_code,
                "error_id": error_id,
                "path": str(request.url.path),
            }
        },
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handle Pydantic ValidationError with clear field error messages.
    """
    error_id = str(uuid.uuid4())
    
    logger.warning(
        f"ValidationError: {len(exc.errors())} errors - Path: {request.url.path} - Error ID: {error_id}"
    )
    
    # Format validation errors for better readability
    formatted_errors = []
    for error in exc.errors():
        formatted_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "message": "Validation failed",
                "type": "validation_error",
                "status_code": 422,
                "error_id": error_id,
                "path": str(request.url.path),
                "details": formatted_errors,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other exceptions with logging and generic error message.
    Never exposes stack traces to the client.
    """
    error_id = str(uuid.uuid4())
    
    # Log full error with traceback
    logger.exception(
        f"Unhandled exception: {type(exc).__name__} - Path: {request.url.path} - Error ID: {error_id}"
    )
    
    # Return generic error message
    message = "An unexpected server error occurred" if not settings.DEBUG else str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": message,
                "type": "server_error",
                "status_code": 500,
                "error_id": error_id,
                "path": str(request.url.path),
            }
        },
    )
