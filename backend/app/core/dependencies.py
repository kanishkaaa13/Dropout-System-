"""
core/dependencies.py
───────────────────
Reusable FastAPI dependencies for authentication, database sessions,
and role-based access control.

Usage:
    from backend.app.core.dependencies import (
        get_db,
        get_current_user,
        get_current_active_user,
        require_role,
    )
"""

from __future__ import annotations

from typing import Annotated, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_async_db
from backend.app.core.security import verify_token

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> dict:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials from request header
        db: Database session
        
    Returns:
        User data from database
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = verify_token(token, token_type="access")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Fetch user from database
    # For now, return mock user data
    # In production, query the User model:
    # user = await db.execute(select(User).where(User.id == user_id))
    # if user is None:
    #     raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user_id,
        "email": payload.get("email"),
        "role": payload.get("role"),
    }


async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """
    Dependency to get the current active user.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        User data if active
        
    Raises:
        HTTPException: If user is inactive
    """
    # TODO: Add is_active field to User model
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user


def require_role(*allowed_roles: str):
    """
    Factory function to create a role-based access control dependency.
    
    Args:
        *allowed_roles: Allowed roles for this endpoint
        
    Returns:
        Dependency function that checks user role
        
    Usage:
        @router.get("/admin")
        async def admin_endpoint(
            user: Annotated[dict, Depends(require_role("admin"))]
        ):
            ...
    """
    async def role_checker(
        current_user: Annotated[dict, Depends(get_current_active_user)]
    ) -> dict:
        user_role = current_user.get("role")
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}",
            )
        
        return current_user
    
    return role_checker


# Common role dependencies
get_admin_user = require_role("admin")
get_faculty_user = require_role("faculty", "admin")
get_student_user = require_role("student", "faculty", "admin")
