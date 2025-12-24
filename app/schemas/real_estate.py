"""
Real Estate schemas for Property and Viewing CRUD operations.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.real_estate import PropertyStatus, PropertyType


# ============== Property Schemas ==============

class PropertyBase(BaseModel):
    """Base property schema."""
    title: str = Field(..., min_length=1, max_length=255)
    address: str = Field(..., min_length=1, max_length=500)
    price: Optional[Decimal] = Field(None, ge=0)
    property_type: PropertyType = PropertyType.HOUSE
    status: PropertyStatus = PropertyStatus.AVAILABLE
    description: Optional[str] = None
    bedrooms: Optional[str] = None
    bathrooms: Optional[str] = None
    area_sqm: Optional[Decimal] = Field(None, ge=0)


class PropertyCreate(PropertyBase):
    """Schema for creating a property."""
    pass


class PropertyUpdate(BaseModel):
    """Schema for updating a property (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    price: Optional[Decimal] = Field(None, ge=0)
    property_type: Optional[PropertyType] = None
    status: Optional[PropertyStatus] = None
    description: Optional[str] = None
    bedrooms: Optional[str] = None
    bathrooms: Optional[str] = None
    area_sqm: Optional[Decimal] = Field(None, ge=0)


class PropertyRead(PropertyBase):
    """Schema for reading property data."""
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============== Viewing Schemas ==============

class ViewingBase(BaseModel):
    """Base viewing schema."""
    viewing_date: datetime
    notes: Optional[str] = None
    status: str = "SCHEDULED"


class ViewingCreate(ViewingBase):
    """Schema for creating a viewing."""
    property_id: UUID
    contact_id: UUID


class ViewingUpdate(BaseModel):
    """Schema for updating a viewing (all fields optional)."""
    viewing_date: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class ViewingRead(ViewingBase):
    """Schema for reading viewing data."""
    id: UUID
    property_id: UUID
    contact_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
