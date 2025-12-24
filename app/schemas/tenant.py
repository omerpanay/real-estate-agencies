"""
Tenant schemas for request/response validation.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TenantBase(BaseModel):
    """Base tenant schema with common fields."""
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$")


class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""
    pass


class TenantRead(TenantBase):
    """Schema for reading tenant data."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TenantUpdate(BaseModel):
    """Schema for updating tenant data."""
    name: str | None = Field(None, min_length=2, max_length=255)
    slug: str | None = Field(None, min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$")
    is_active: bool | None = None
