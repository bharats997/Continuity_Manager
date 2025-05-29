# backend/app/apis/endpoints/roles.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...models.role import Role as RoleSchema
from ...models.person import Person as PersonSchema # Import Person schema for current_user
from ...services.role_service import role_service
from ..deps import get_db, get_current_active_user, allow_people_read # Use a general read permission

router = APIRouter()

@router.get("/", response_model=List[RoleSchema], dependencies=[Depends(allow_people_read)])
def list_roles(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: PersonSchema = Depends(get_current_active_user) # User performing the action
):
    """
    Retrieve all roles.
    Accessible by users with permission to read people/role information.
    """
    roles = role_service.get_roles(db, skip=skip, limit=limit)
    return roles

@router.get("/{role_id}", response_model=RoleSchema, dependencies=[Depends(allow_people_read)])
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: PersonSchema = Depends(get_current_active_user) # User performing the action
):
    """
    Get a specific role by ID.
    """
    role = role_service.get_role_by_id(db, role_id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role

