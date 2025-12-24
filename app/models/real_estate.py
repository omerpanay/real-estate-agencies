"""
Real Estate module models: Property and Viewing with multi-tenant support.
"""
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Column, DateTime, Enum, ForeignKey, 
    Numeric, String, Text
)
from sqlalchemy import Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TenantMixin


class PropertyType(str, enum.Enum):
    """Enum for property types."""
    HOUSE = "HOUSE"
    APARTMENT = "APARTMENT"
    COMMERCIAL = "COMMERCIAL"
    LAND = "LAND"


class PropertyStatus(str, enum.Enum):
    """Enum for property status."""
    AVAILABLE = "AVAILABLE"
    SOLD = "SOLD"
    RENTED = "RENTED"
    PENDING = "PENDING"


class Property(TenantMixin, Base):
    """
    Property model representing a real estate listing.
    
    Each property belongs to a tenant via TenantMixin.
    """
    __tablename__ = "properties"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    address = Column(String(500), nullable=False)
    price = Column(Numeric(15, 2), nullable=True)
    property_type = Column(
        Enum(PropertyType), 
        default=PropertyType.HOUSE, 
        nullable=False,
        index=True
    )
    status = Column(
        Enum(PropertyStatus), 
        default=PropertyStatus.AVAILABLE, 
        nullable=False,
        index=True
    )
    description = Column(Text, nullable=True)
    bedrooms = Column(String(10), nullable=True)
    bathrooms = Column(String(10), nullable=True)
    area_sqm = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    viewings = relationship("Viewing", back_populates="property", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Property(id={self.id}, title='{self.title}', status={self.status})>"


class Viewing(TenantMixin, Base):
    """
    Viewing model representing a property viewing appointment.
    
    Links a Contact to a Property with viewing details.
    """
    __tablename__ = "viewings"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(
        Uuid(as_uuid=True), 
        ForeignKey("properties.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    contact_id = Column(
        Uuid(as_uuid=True), 
        ForeignKey("contacts.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    viewing_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default="SCHEDULED", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    property = relationship("Property", back_populates="viewings")
    contact = relationship("Contact")
    
    def __repr__(self) -> str:
        return f"<Viewing(id={self.id}, property_id={self.property_id}, date={self.viewing_date})>"
