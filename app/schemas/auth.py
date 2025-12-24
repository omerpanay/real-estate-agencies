"""
Authentication schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Response schema for JWT token."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded JWT token data."""
    user_id: Optional[UUID] = None
    tenant_id: Optional[UUID] = None


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    tenant_id: UUID


class UserRead(UserBase):
    """Schema for reading user data."""
    id: UUID
    tenant_id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login request."""
    email: EmailStr
    password: str
