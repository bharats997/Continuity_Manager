# backend/app/apis/endpoints/locations.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...services import location_service # Updated import
from ...models.location import Location, LocationCreate, LocationUpdate, LocationListResponse
from ...models.domain.people import Person # For current_user dependency, changed from .users import User
from ..deps import get_db, get_current_active_user # Assuming get_current_active_user for auth

router = APIRouter()

@router.post("/", response_model=Location, status_code=status.HTTP_201_CREATED)
def create_location(
    location_in: LocationCreate,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_active_user) # Assuming authentication
):
    """
    Create a new location. 
    The organizationId must be provided in the request body.
    The current user's organization will be implicitly used or validated if needed.
    (Currently, service expects organizationId in location_in)
    """
    # Optional: Add authorization check if current_user.organizationId should match location_in.organizationId
    # if current_user.organizationId != location_in.organizationId:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="You do not have permission to create locations for this organization."
    #     )
    return location_service.create_location(db=db, location_in=location_in)

@router.get("/{location_id}", response_model=Location)
def read_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_active_user)
):
    """
    Get a specific location by ID.
    """
    db_location = location_service.get_location(db, location_id=location_id)
    if not db_location: # Service already raises 404, but an explicit check here is also fine
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    # Optional: Authorization check if user belongs to the location's organization
    # if db_location.organizationId != current_user.organizationId:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this location")
    return db_location

@router.get("/organization/{organization_id}/", response_model=LocationListResponse)
def read_locations_for_organization(
    organization_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_active_user)
):
    """
    Retrieve all locations for a specific organization.
    """
    # Optional: Authorization check
    # if organization_id != current_user.organizationId:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access locations for this organization")
    locations = location_service.get_all_locations_for_organization(
        db, organization_id=organization_id, skip=skip, limit=limit
    )
    return {"items": locations, "total": len(locations)} # A more accurate total would require a count query

@router.put("/{location_id}", response_model=Location)
def update_location(
    location_id: int,
    location_in: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_active_user)
):
    """
    Update a location.
    """
    db_location = location_service.get_location(db, location_id=location_id) # Check existence and ownership
    # Optional: Authorization check
    # if db_location.organizationId != current_user.organizationId:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this location")
    return location_service.update_location(db=db, location_id=location_id, location_in=location_in)

@router.delete("/{location_id}", response_model=Location)
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_active_user)
):
    """
    Delete a location.
    """
    db_location = location_service.get_location(db, location_id=location_id) # Check existence and ownership
    # Optional: Authorization check
    # if db_location.organizationId != current_user.organizationId:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this location")
    return location_service.delete_location(db=db, location_id=location_id)
