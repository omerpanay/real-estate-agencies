"""
Dependency injection functions for FastAPI.
"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.tenant import User
from app.schemas.auth import TokenData


# OAuth2 scheme for extracting JWT from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Dependency that extracts and validates the JWT token,
    then returns the current authenticated user.
    
    Args:
        token: JWT token from Authorization header (Bearer token).
        db: Database session.
        
    Returns:
        The authenticated User object.
        
    Raises:
        HTTPException: If token is invalid or user not found/inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode and verify the token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # Extract user_id and tenant_id from token
    user_id_str: str | None = payload.get("sub")
    tenant_id_str: str | None = payload.get("tenant_id")
    
    if user_id_str is None or tenant_id_str is None:
        raise credentials_exception
    
    try:
        user_id = UUID(user_id_str)
        tenant_id = UUID(tenant_id_str)
    except ValueError:
        raise credentials_exception
    
    # Create token data for reference
    token_data = TokenData(user_id=user_id, tenant_id=tenant_id)
    
    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == token_data.user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    # Verify user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    # Verify tenant_id matches (security check)
    if user.tenant_id != token_data.tenant_id:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency that ensures the current user is active.
    This is a convenience wrapper around get_current_user.
    
    Args:
        current_user: The current authenticated user.
        
    Returns:
        The active User object.
    """
    # Already checked in get_current_user, but kept for explicit endpoint requirements
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency that ensures the current user is a superuser.
    
    Args:
        current_user: The current authenticated user.
        
    Returns:
        The superuser User object.
        
    Raises:
        HTTPException: If user is not a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
