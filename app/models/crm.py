"""
CRM models: Contact and Deal with multi-tenant support.
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


class DealStage(str, enum.Enum):
    """Enum for deal stages."""
    NEW = "NEW"
    NEGOTIATION = "NEGOTIATION"
    CLOSED_WON = "CLOSED_WON"
    CLOSED_LOST = "CLOSED_LOST"


class Contact(TenantMixin, Base):
    """
    Contact model representing a customer/lead.
    
    Each contact belongs to a tenant via TenantMixin.
    """
    __tablename__ = "contacts"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    deals = relationship("Deal", back_populates="contact", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, name='{self.first_name} {self.last_name}')>"


class Deal(TenantMixin, Base):
    """
    Deal model representing a sales opportunity.
    
    Each deal belongs to a tenant and is linked to a contact.
    """
    __tablename__ = "deals"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id = Column(
        Uuid(as_uuid=True), 
        ForeignKey("contacts.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    title = Column(String(255), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=True)
    stage = Column(
        Enum(DealStage), 
        default=DealStage.NEW, 
        nullable=False,
        index=True
    )
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    contact = relationship("Contact", back_populates="deals")
    
    def __repr__(self) -> str:
        return f"<Deal(id={self.id}, title='{self.title}', stage={self.stage})>"
