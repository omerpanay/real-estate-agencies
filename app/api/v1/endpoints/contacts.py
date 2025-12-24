"""
Contact endpoints with tenant-scoped CRUD operations.
"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.crm import Contact
from app.models.tenant import User
from app.schemas.crm import ContactCreate, ContactRead, ContactUpdate


router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.post("/", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_in: ContactCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Contact:
    """
    Create a new contact for the current tenant.
    
    The tenant_id is automatically assigned from the authenticated user.
    """
    # Create contact with tenant_id from current user
    contact = Contact(
        **contact_in.model_dump(),
        tenant_id=current_user.tenant_id,
    )
    
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    
    return contact


@router.get("/", response_model=list[ContactRead])
async def list_contacts(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    search: Optional[str] = Query(None, description="Search by name or email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[Contact]:
    """
    List all contacts for the current tenant.
    
    Supports optional search by first_name, last_name, or email.
    """
    # Base query filtered by tenant_id
    query = select(Contact).where(Contact.tenant_id == current_user.tenant_id)
    
    # Apply search filter if provided
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Contact.first_name.ilike(search_pattern),
                Contact.last_name.ilike(search_pattern),
                Contact.email.ilike(search_pattern),
            )
        )
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Contact.created_at.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{contact_id}", response_model=ContactRead)
async def get_contact(
    contact_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Contact:
    """
    Get a specific contact by ID.
    
    Ensures the contact belongs to the current tenant.
    """
    result = await db.execute(
        select(Contact).where(
            Contact.id == contact_id,
            Contact.tenant_id == current_user.tenant_id,
        )
    )
    contact = result.scalar_one_or_none()
    
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    
    return contact


@router.patch("/{contact_id}", response_model=ContactRead)
async def update_contact(
    contact_id: UUID,
    contact_in: ContactUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Contact:
    """
    Update a contact by ID.
    
    Only updates fields that are provided in the request.
    """
    result = await db.execute(
        select(Contact).where(
            Contact.id == contact_id,
            Contact.tenant_id == current_user.tenant_id,
        )
    )
    contact = result.scalar_one_or_none()
    
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    
    # Update only provided fields
    update_data = contact_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)
    
    await db.commit()
    await db.refresh(contact)
    
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Delete a contact by ID.
    
    Also deletes all associated deals (cascade).
    """
    result = await db.execute(
        select(Contact).where(
            Contact.id == contact_id,
            Contact.tenant_id == current_user.tenant_id,
        )
    )
    contact = result.scalar_one_or_none()
    
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    
    await db.delete(contact)
    await db.commit()
