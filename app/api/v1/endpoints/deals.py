"""
Deal endpoints with tenant-scoped CRUD operations.
"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.crm import Contact, Deal, DealStage
from app.models.tenant import User
from app.schemas.crm import DealCreate, DealRead, DealReadWithContact, DealUpdate


router = APIRouter(prefix="/deals", tags=["Deals"])


@router.post("/", response_model=DealRead, status_code=status.HTTP_201_CREATED)
async def create_deal(
    deal_in: DealCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Deal:
    """
    Create a new deal for the current tenant.
    
    The contact must belong to the same tenant.
    The tenant_id is automatically assigned from the authenticated user.
    """
    # Verify the contact exists and belongs to the same tenant
    result = await db.execute(
        select(Contact).where(
            Contact.id == deal_in.contact_id,
            Contact.tenant_id == current_user.tenant_id,
        )
    )
    contact = result.scalar_one_or_none()
    
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found or does not belong to your tenant",
        )
    
    # Create deal with tenant_id from current user
    deal = Deal(
        **deal_in.model_dump(),
        tenant_id=current_user.tenant_id,
    )
    
    db.add(deal)
    await db.commit()
    await db.refresh(deal)
    
    return deal


@router.get("/", response_model=list[DealRead])
async def list_deals(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    stage: Optional[DealStage] = Query(None, description="Filter by deal stage"),
    contact_id: Optional[UUID] = Query(None, description="Filter by contact ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[Deal]:
    """
    List all deals for the current tenant.
    
    Supports optional filtering by stage and contact_id.
    """
    # Base query filtered by tenant_id
    query = select(Deal).where(Deal.tenant_id == current_user.tenant_id)
    
    # Apply optional filters
    if stage:
        query = query.where(Deal.stage == stage)
    if contact_id:
        query = query.where(Deal.contact_id == contact_id)
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Deal.created_at.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{deal_id}", response_model=DealReadWithContact)
async def get_deal(
    deal_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Deal:
    """
    Get a specific deal by ID with contact details.
    
    Ensures the deal belongs to the current tenant.
    """
    result = await db.execute(
        select(Deal)
        .where(
            Deal.id == deal_id,
            Deal.tenant_id == current_user.tenant_id,
        )
        .options(selectinload(Deal.contact))
    )
    deal = result.scalar_one_or_none()
    
    if deal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )
    
    return deal


@router.patch("/{deal_id}", response_model=DealRead)
async def update_deal(
    deal_id: UUID,
    deal_in: DealUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Deal:
    """
    Update a deal by ID.
    
    If changing contact_id, the new contact must belong to the same tenant.
    """
    result = await db.execute(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.tenant_id == current_user.tenant_id,
        )
    )
    deal = result.scalar_one_or_none()
    
    if deal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )
    
    update_data = deal_in.model_dump(exclude_unset=True)
    
    # If updating contact_id, verify the new contact belongs to the same tenant
    if "contact_id" in update_data and update_data["contact_id"] is not None:
        result = await db.execute(
            select(Contact).where(
                Contact.id == update_data["contact_id"],
                Contact.tenant_id == current_user.tenant_id,
            )
        )
        contact = result.scalar_one_or_none()
        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found or does not belong to your tenant",
            )
    
    # Update only provided fields
    for field, value in update_data.items():
        setattr(deal, field, value)
    
    await db.commit()
    await db.refresh(deal)
    
    return deal


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Delete a deal by ID.
    """
    result = await db.execute(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.tenant_id == current_user.tenant_id,
        )
    )
    deal = result.scalar_one_or_none()
    
    if deal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )
    
    await db.delete(deal)
    await db.commit()
