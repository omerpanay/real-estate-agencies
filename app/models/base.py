"""
Base model and TenantMixin for multi-tenant architecture.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import declared_attr


class TenantMixin:
    """
    Mixin that adds tenant_id column for multi-tenant models.
    
    All models that inherit from this mixin will automatically
    have a tenant_id column that references the tenants table.
    """
    
    @declared_attr
    def tenant_id(cls):
        return Column(
            Uuid(as_uuid=True),
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,  # Index is created here, no need for __table_args__
        )
