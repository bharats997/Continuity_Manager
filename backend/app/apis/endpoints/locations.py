# backend/app/apis/endpoints/locations.py
import uuid  # Import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...services import location_service # Updated import
from ...schemas.location import LocationSchema, LocationCreate, LocationUpdate, LocationListResponse
from ...schemas.user_schemas import UserSchema # For current_user dependency
from ..deps import get_async_db, get_current_active_user # Assuming get_current_active_user for auth

router = APIRouter()

@router.post("/", response_model=LocationSchema, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_in: LocationCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserSchema = Depends(get_current_active_user) # Assuming authentication
):
    """
    Create a new location. 
    The organizationId must be provided in the request body.
    The current user's organization will be implicitly used or validated if needed.
    (Currently, service expects organizationId in location_in)
    """
    if current_user.organizationId != location_in.organizationId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create locations for this organization."
        )
    return await location_service.create_location(db=db, location_in=location_in)

@router.get("/{location_id}", response_model=LocationSchema)
async def read_location(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserSchema = Depends(get_current_active_user)
):
    """
    Get a specific location by ID.
    """
    db_location = location_service.get_location(db, location_id=location_id)
    if not db_location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    if db_location.organizationId != current_user.organizationId:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this location")
    return db_location

@router.get("/organization/{organization_id}/", response_model=LocationListResponse)
async def read_locations_for_organization(
    organization_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_async_db),
    current_user: UserSchema = Depends(get_current_active_user)
):
    """
    Retrieve all locations for a specific organization.
    """
    if organization_id != current_user.organizationId:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access locations for this organization")
    locations = await location_service.get_all_locations_for_organization(
        db, organization_id=organization_id, skip=skip, limit=limit
    )
    # TODO: Implement a count query in the service for accurate total
    count = await location_service.count_locations_for_organization(db, organization_id=organization_id) 
    return {"items": locations, "total": count}

@router.put("/{location_id}", response_model=LocationSchema)
async def update_location(
    location_id: uuid.UUID,
    location_in: LocationUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserSchema = Depends(get_current_active_user)
):
    """
    Update a location.
    """
    db_location = location_service.get_location(db, location_id=location_id)
    if not db_location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    if db_location.organizationId != current_user.organizationId:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this location")
    return await location_service.update_location(db=db, location_id=location_id, location_in=location_in)

@router.delete("/{location_id}", response_model=LocationSchema)
async def delete_location(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserSchema = Depends(get_current_active_user)
):
    """
    Delete a location.
    """
    db_location = location_service.get_location(db, location_id=location_id)
    if not db_location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    if db_location.organizationId != current_user.organizationId:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this location")
    return await location_service.delete_location(db=db, location_id=location_id)
