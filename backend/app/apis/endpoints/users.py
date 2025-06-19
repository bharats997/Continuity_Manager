# backend/app/apis/endpoints/users.py
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...schemas.user_schemas import UserSchema, UserCreate, UserUpdate
from ...models.domain.users import User as UserDB
from ...services.user_service import user_service
from ..deps import get_async_db, get_current_active_user, allow_user_management, allow_user_read

router = APIRouter()

@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(allow_user_management)])
async def create_user_endpoint(
    *,
    db: AsyncSession = Depends(get_async_db),
    user_in: UserCreate,
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    Create a new user.
    Only accessible by users with 'Admin' role (via allow_user_management).
    """
    organization_id = current_user.organization_id
    creator_id = current_user.id

    return await user_service.create_user(
        db=db, user_in=user_in, organization_id=organization_id, current_user_id=creator_id
    )

@router.get("/", response_model=List[UserSchema], dependencies=[Depends(allow_user_read)])
async def list_users_endpoint(
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = Query(True, description="Filter by active status. Set to null to get all."),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    Retrieve users within the user's organization.
    Accessible by users with general read permissions for users.
    """
    organization_id = current_user.organization_id
    users = await user_service.get_users(
        db, organization_id=organization_id, skip=skip, limit=limit, is_active=is_active
    )
    return users

@router.get("/{user_id}", response_model=UserSchema, dependencies=[Depends(allow_user_read)])
async def get_user_endpoint(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    Get a specific user by ID within the user's organization.
    """
    organization_id = current_user.organization_id
    user = await user_service.get_user_by_id(db, user_id=user_id, organization_id=organization_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserSchema, dependencies=[Depends(allow_user_management)])
async def update_user_endpoint(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    Update a user.
    Only accessible by users with 'Admin' role.
    """
    organization_id = current_user.organization_id
    user_db = await user_service.get_user_by_id(db, user_id=user_id, organization_id=organization_id)
    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    updater_id = current_user.id

    return await user_service.update_user(db=db, user_db=user_db, user_in=user_in, current_user_id=updater_id)

@router.delete("/{user_id}", response_model=UserSchema, dependencies=[Depends(allow_user_management)])
async def soft_delete_user_endpoint(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    Soft delete a user (mark as inactive).
    Only accessible by users with 'Admin' role.
    """
    organization_id = current_user.organization_id
    user_db = await user_service.get_user_by_id(db, user_id=user_id, organization_id=organization_id)
    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updater_id = current_user.id

    return await user_service.soft_delete_user(db=db, user_db=user_db, current_user_id=updater_id)
