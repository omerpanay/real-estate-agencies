"""
Tenant and User models for multi-tenant architecture.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TenantMixin


class Tenant(Base):
    """
    Tenant model representing an organization/company in the system.
    """
    __tablename__ = "tenants"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name='{self.name}')>"


class User(TenantMixin, Base):
    """
    User model belonging to a tenant.
    
    Uses TenantMixin to automatically add tenant_id column.
    Email is unique per tenant (not globally unique).
    """
    __tablename__ = "users"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    
    # Unique constraint: email must be unique within a tenant
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', tenant_id={self.tenant_id})>"
