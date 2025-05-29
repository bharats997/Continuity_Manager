# backend/app/apis/endpoints/people.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...models.person import Person as PersonSchema, PersonCreate, PersonUpdate
from ...models.domain.people import Person as PersonDB # For current_user type hint from deps
from ...services.person_service import person_service
from ..deps import get_db, get_current_active_user, allow_people_management, allow_people_read

router = APIRouter()

@router.post("/", response_model=PersonSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(allow_people_management)])
def create_person_endpoint(
    *,
    db: Session = Depends(get_db),
    person_in: PersonCreate,
    current_user: PersonDB = Depends(get_current_active_user) # User performing the action
):
    """
    Create a new person.
    Only accessible by users with 'Admin' role (via allow_people_management).
    """
    # organization_id will be derived from the current_user in a real auth system
    # For placeholder, current_user from deps has organizationId
    organization_id = current_user.organizationId
    
    # Ensure current_user.id is an int
    creator_id = current_user.id
    if not isinstance(creator_id, int):
        # This case should ideally not happen if current_user is correctly populated
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is invalid")

    return person_service.create_person(
        db=db, person_in=person_in, organization_id=organization_id, current_user_id=creator_id
    )

@router.get("/", response_model=List[PersonSchema], dependencies=[Depends(allow_people_read)])
def list_people_endpoint(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = Query(True, description="Filter by active status. Set to null to get all."),
    current_user: PersonDB = Depends(get_current_active_user)
):
    """
    Retrieve people within the user's organization.
    Accessible by users with general read permissions for people.
    """
    organization_id = current_user.organizationId
    people = person_service.get_people(
        db, organization_id=organization_id, skip=skip, limit=limit, is_active=is_active
    )
    return people

@router.get("/{person_id}", response_model=PersonSchema, dependencies=[Depends(allow_people_read)])
def get_person_endpoint(
    person_id: int,
    db: Session = Depends(get_db),
    current_user: PersonDB = Depends(get_current_active_user)
):
    """
    Get a specific person by ID within the user's organization.
    """
    organization_id = current_user.organizationId
    person = person_service.get_person_by_id(db, person_id=person_id, organization_id=organization_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    return person

@router.put("/{person_id}", response_model=PersonSchema, dependencies=[Depends(allow_people_management)])
def update_person_endpoint(
    person_id: int,
    person_in: PersonUpdate,
    db: Session = Depends(get_db),
    current_user: PersonDB = Depends(get_current_active_user)
):
    """
    Update a person.
    Only accessible by users with 'Admin' role.
    """
    organization_id = current_user.organizationId
    person_db = person_service.get_person_by_id(db, person_id=person_id, organization_id=organization_id)
    if not person_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    
    updater_id = current_user.id
    if not isinstance(updater_id, int):
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is invalid for updater")

    return person_service.update_person(db=db, person_db=person_db, person_in=person_in, current_user_id=updater_id)

@router.delete("/{person_id}", response_model=PersonSchema, dependencies=[Depends(allow_people_management)])
def soft_delete_person_endpoint( # Changed from delete to soft_delete
    person_id: int,
    db: Session = Depends(get_db),
    current_user: PersonDB = Depends(get_current_active_user)
):
    """
    Soft delete a person (mark as inactive).
    Only accessible by users with 'Admin' role.
    """
    organization_id = current_user.organizationId
    person_db = person_service.get_person_by_id(db, person_id=person_id, organization_id=organization_id)
    if not person_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    updater_id = current_user.id
    if not isinstance(updater_id, int):
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is invalid for updater")

    return person_service.soft_delete_person(db=db, person_db=person_db, current_user_id=updater_id)

