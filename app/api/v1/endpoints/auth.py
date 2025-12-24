"""
Authentication endpoints.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.tenant import User
from app.schemas.auth import Token


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """
    OAuth2 compatible token login endpoint.
    
    Authenticates user with email/password and returns a JWT access token
    containing user_id and tenant_id.
    
    Args:
        form_data: OAuth2 form with username (email) and password.
        db: Database session.
        
    Returns:
        Token object with access_token and token_type.
        
    Raises:
        HTTPException: If credentials are invalid.
    """
    # Query user by email (username field contains email)
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and password is correct
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    
    # Create access token with user_id and tenant_id
    access_token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/login/json", response_model=Token)
async def login_json(
    email: str,
    password: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """
    JSON-based login endpoint (alternative to OAuth2 form).
    
    Authenticates user with email/password and returns a JWT access token.
    
    Args:
        email: User's email address.
        password: User's password.
        db: Database session.
        
    Returns:
        Token object with access_token and token_type.
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    
    access_token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
    )
    
    return Token(access_token=access_token, token_type="bearer")
