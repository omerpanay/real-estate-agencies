"""
CRM schemas for Contact and Deal CRUD operations.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.crm import DealStage


# ============== Contact Schemas ==============

class ContactBase(BaseModel):
    """Base contact schema."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class ContactCreate(ContactBase):
    """Schema for creating a contact."""
    pass


class ContactUpdate(BaseModel):
    """Schema for updating a contact (all fields optional)."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class ContactRead(ContactBase):
    """Schema for reading contact data."""
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============== Deal Schemas ==============

class DealBase(BaseModel):
    """Base deal schema."""
    title: str = Field(..., min_length=1, max_length=255)
    amount: Optional[Decimal] = Field(None, ge=0)
    stage: DealStage = DealStage.NEW
    description: Optional[str] = None


class DealCreate(DealBase):
    """Schema for creating a deal."""
    contact_id: UUID


class DealUpdate(BaseModel):
    """Schema for updating a deal (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[Decimal] = Field(None, ge=0)
    stage: Optional[DealStage] = None
    description: Optional[str] = None
    contact_id: Optional[UUID] = None


class DealRead(DealBase):
    """Schema for reading deal data."""
    id: UUID
    contact_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DealReadWithContact(DealRead):
    """Schema for reading deal with nested contact."""
    contact: ContactRead
