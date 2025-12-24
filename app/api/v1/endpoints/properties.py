"""
Property endpoints with tenant-scoped CRUD operations.
"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.crm import Contact
from app.models.real_estate import Property, PropertyStatus, PropertyType, Viewing
from app.models.tenant import User
from app.schemas.real_estate import (
    PropertyCreate, PropertyRead, PropertyUpdate,
    ViewingCreate, ViewingRead, ViewingUpdate
)


router = APIRouter(prefix="/properties", tags=["Properties"])


# ============== Property Endpoints ==============

@router.post("/", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
async def create_property(
    property_in: PropertyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Property:
    """
    Create a new property for the current tenant.
    
    The tenant_id is automatically assigned from the authenticated user.
    """
    property_obj = Property(
        **property_in.model_dump(),
        tenant_id=current_user.tenant_id,
    )
    
    db.add(property_obj)
    await db.commit()
    await db.refresh(property_obj)
    
    return property_obj


@router.get("/", response_model=list[PropertyRead])
async def list_properties(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    property_type: Optional[PropertyType] = Query(None, description="Filter by property type"),
    status_filter: Optional[PropertyStatus] = Query(None, alias="status", description="Filter by status"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[Property]:
    """
    List all properties for the current tenant.
    
    Supports optional filtering by type, status, and price range.
    """
    query = select(Property).where(Property.tenant_id == current_user.tenant_id)
    
    if property_type:
        query = query.where(Property.property_type == property_type)
    if status_filter:
        query = query.where(Property.status == status_filter)
    if min_price is not None:
        query = query.where(Property.price >= min_price)
    if max_price is not None:
        query = query.where(Property.price <= max_price)
    
    query = query.offset(skip).limit(limit).order_by(Property.created_at.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{property_id}", response_model=PropertyRead)
async def get_property(
    property_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Property:
    """
    Get a specific property by ID.
    
    Ensures the property belongs to the current tenant.
    """
    result = await db.execute(
        select(Property).where(
            Property.id == property_id,
            Property.tenant_id == current_user.tenant_id,
        )
    )
    property_obj = result.scalar_one_or_none()
    
    if property_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    return property_obj


@router.patch("/{property_id}", response_model=PropertyRead)
async def update_property(
    property_id: UUID,
    property_in: PropertyUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Property:
    """
    Update a property by ID.
    """
    result = await db.execute(
        select(Property).where(
            Property.id == property_id,
            Property.tenant_id == current_user.tenant_id,
        )
    )
    property_obj = result.scalar_one_or_none()
    
    if property_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    update_data = property_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(property_obj, field, value)
    
    await db.commit()
    await db.refresh(property_obj)
    
    return property_obj


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Delete a property by ID.
    """
    result = await db.execute(
        select(Property).where(
            Property.id == property_id,
            Property.tenant_id == current_user.tenant_id,
        )
    )
    property_obj = result.scalar_one_or_none()
    
    if property_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    await db.delete(property_obj)
    await db.commit()


# ============== Viewing Endpoints ==============

@router.post("/{property_id}/viewings", response_model=ViewingRead, status_code=status.HTTP_201_CREATED)
async def create_viewing(
    property_id: UUID,
    viewing_in: ViewingCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Viewing:
    """
    Schedule a viewing for a property.
    
    Both property and contact must belong to the same tenant.
    """
    # Verify property exists and belongs to tenant
    result = await db.execute(
        select(Property).where(
            Property.id == property_id,
            Property.tenant_id == current_user.tenant_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    # Verify contact exists and belongs to tenant
    result = await db.execute(
        select(Contact).where(
            Contact.id == viewing_in.contact_id,
            Contact.tenant_id == current_user.tenant_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    
    viewing = Viewing(
        property_id=property_id,
        contact_id=viewing_in.contact_id,
        viewing_date=viewing_in.viewing_date,
        notes=viewing_in.notes,
        status=viewing_in.status,
        tenant_id=current_user.tenant_id,
    )
    
    db.add(viewing)
    await db.commit()
    await db.refresh(viewing)
    
    return viewing


@router.get("/{property_id}/viewings", response_model=list[ViewingRead])
async def list_viewings(
    property_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[Viewing]:
    """
    List all viewings for a property.
    """
    # Verify property exists and belongs to tenant
    result = await db.execute(
        select(Property).where(
            Property.id == property_id,
            Property.tenant_id == current_user.tenant_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    result = await db.execute(
        select(Viewing).where(
            Viewing.property_id == property_id,
            Viewing.tenant_id == current_user.tenant_id,
        ).order_by(Viewing.viewing_date)
    )
    return list(result.scalars().all())
