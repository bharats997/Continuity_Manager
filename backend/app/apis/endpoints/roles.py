# backend/app/apis/endpoints/roles.py
import uuid  # Import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...schemas.role import RoleSchema, RoleCreate, RoleUpdate
from ...schemas.user_schemas import UserSchema # Import Pydantic UserSchema
from ...models.domain.users import User as UserDB # Import SQLAlchemy User model as UserDB
from ...services.role_service import role_service
from ..deps import get_async_db, get_current_active_user, RequirePermission, RolePermissions # Import new permission tools

router = APIRouter()

@router.get("/", response_model=List[RoleSchema], dependencies=[Depends(RequirePermission(RolePermissions.LIST))])
async def list_roles(
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 100,
    name_filter: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    current_user: UserDB = Depends(get_current_active_user) # User performing the action
):
    """
    Retrieve all roles.
    Accessible by users with permission to read people/role information.
    """
    # current_user is PersonDB (SQLAlchemy model) which has organizationId (capital 'I')
    if not current_user.organizationId:
        # This case should ideally not happen if user is always associated with an org.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User organization not found.")
    roles = await role_service.get_roles(db, organization_id=current_user.organizationId, skip=skip, limit=limit, name_filter=name_filter, sort_by=sort_by, sort_order=sort_order)
    return roles

@router.get("/{role_id}", response_model=RoleSchema)
async def get_role(
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserDB = Depends(RequirePermission(RolePermissions.READ))
):
    """
    Get a specific role by ID.
    """
    role = await role_service.get_role_by_id(db, role_id=role_id, organization_id=current_user.organizationId)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.post("/", response_model=RoleSchema, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_in: RoleCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserDB = Depends(RequirePermission(RolePermissions.CREATE))
):
    """
    Create a new role.
    (Permissions for this action to be defined)
    """
    # The service method already handles potential HTTPExceptions for duplicate names or bad permission_ids
    return await role_service.create_role(db=db, role_in=role_in, organization_id=current_user.organizationId)

@router.put("/{role_id}", response_model=RoleSchema)
async def update_role(
    role_id: uuid.UUID,
    role_in: RoleUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserDB = Depends(RequirePermission(RolePermissions.UPDATE))
):
    """
    Update an existing role.
    (Permissions for this action to be defined)
    """
    updated_role = await role_service.update_role(db=db, role_id=role_id, role_in=role_in, organization_id=current_user.organizationId)
    if not updated_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    # The service method handles potential HTTPExceptions for duplicate names or bad permission_ids
    return updated_role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserDB = Depends(RequirePermission(RolePermissions.DELETE))
):
    """
    Delete a role by ID.
    """
    success = await role_service.delete_role(db=db, role_id=role_id, organization_id=current_user.organizationId)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found or could not be deleted")
    return # No content on success
