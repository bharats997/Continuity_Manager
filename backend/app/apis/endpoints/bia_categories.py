import uuid
from typing import Any, List

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.models.domain.users import User
from app.apis import deps
from app.utils.rbac import ensure_user_has_permissions

router = APIRouter()

# Permissions
CREATE_BIA_CATEGORY_PERMISSION = "bia_category_create"
READ_BIA_CATEGORY_PERMISSION = "bia_category_read"
UPDATE_BIA_CATEGORY_PERMISSION = "bia_category_update"
DELETE_BIA_CATEGORY_PERMISSION = "bia_category_delete"


@router.post("/", response_model=schemas.BIACategoryRead, status_code=status.HTTP_201_CREATED)
async def create_bia_category(
    *, 
    db: AsyncSession = Depends(deps.get_async_db),
    bia_category_in: schemas.BIACategoryCreate,
    current_user: User = Depends(ensure_user_has_permissions([CREATE_BIA_CATEGORY_PERMISSION]))
) -> Any:
    logger = logging.getLogger(__name__)
    logger.info(f"Creating BIA category. current_user.id: {current_user.id}, current_user.organization_id: {current_user.organization_id}")
    """
    Create new BIA category.
    Requires 'bia_category_create' permission.
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User has no organization assigned.")

    existing_category = await crud.bia_category.get_by_name_and_organization(
        db, name=bia_category_in.name, organization_id=current_user.organization_id
    )
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A BIA category with this name already exists in your organization.",
        )
    bia_category = await crud.bia_category.create(db=db, obj_in=bia_category_in, organization_id=current_user.organization_id, created_by_id=current_user.id)
    return bia_category


@router.get("/", response_model=List[schemas.BIACategoryRead])
async def read_bia_categories(
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(ensure_user_has_permissions([READ_BIA_CATEGORY_PERMISSION]))
) -> Any:
    """
    Retrieve BIA categories for the user's organization.
    Requires 'bia_category_read' permission.
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User has no organization assigned.")
    
    bia_categories = await crud.bia_category.get_multi_by_organization(
        db, organization_id=current_user.organization_id, skip=skip, limit=limit
    )
    return bia_categories


@router.get("/{id}", response_model=schemas.BIACategoryRead)
async def read_bia_category(
    *, 
    db: AsyncSession = Depends(deps.get_async_db),
    id: uuid.UUID,
    current_user: User = Depends(ensure_user_has_permissions([READ_BIA_CATEGORY_PERMISSION]))
) -> Any:
    """
    Get BIA category by ID for the user's organization.
    Requires 'bia_category_read' permission.
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User has no organization assigned.")

    bia_category = await crud.bia_category.get(db=db, id=id)
    if not bia_category or bia_category.organization_id != str(current_user.organization_id) or not bia_category.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BIA Category not found")
    return bia_category


@router.put("/{id}", response_model=schemas.BIACategoryRead)
async def update_bia_category(
    *, 
    db: AsyncSession = Depends(deps.get_async_db),
    id: uuid.UUID,
    bia_category_in: schemas.BIACategoryUpdate,
    current_user: User = Depends(ensure_user_has_permissions([UPDATE_BIA_CATEGORY_PERMISSION]))
) -> Any:
    """
    Update a BIA category for the user's organization.
    Requires 'bia_category_update' permission.
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User has no organization assigned.")

    bia_category_db_obj = await crud.bia_category.get(db=db, id=id)
    if not bia_category_db_obj or bia_category_db_obj.organization_id != str(current_user.organization_id) or not bia_category_db_obj.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BIA Category not found")

    # Check for name conflict if name is being changed
    if bia_category_in.name and bia_category_in.name != bia_category_db_obj.name:
        existing_category = await crud.bia_category.get_by_name_and_organization(
            db, name=bia_category_in.name, organization_id=current_user.organization_id
        )
        if existing_category and existing_category.id != id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A BIA category with this name already exists in your organization.",
            )
    
    updated_bia_category = await crud.bia_category.update(db=db, db_obj=bia_category_db_obj, obj_in=bia_category_in)
    return updated_bia_category


@router.delete("/{id}", response_model=schemas.BIACategoryRead)
async def delete_bia_category(
    *, 
    db: AsyncSession = Depends(deps.get_async_db),
    id: uuid.UUID,
    current_user: User = Depends(ensure_user_has_permissions([DELETE_BIA_CATEGORY_PERMISSION]))
) -> Any:
    """
    Soft delete a BIA category for the user's organization.
    Requires 'bia_category_delete' permission.
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User has no organization assigned.")

    deleted_bia_category = await crud.bia_category.soft_delete(db=db, id=id, organization_id=current_user.organization_id)
    if not deleted_bia_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BIA Category not found or does not belong to user's organization")
    return deleted_bia_category
