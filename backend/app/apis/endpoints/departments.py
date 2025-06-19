# backend/app/apis/endpoints/departments.py
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import deps
from ...schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)
from ...schemas.user_schemas import UserSchema
from ...services import department_service
from ..deps import DepartmentPermissions, RequirePermission

router = APIRouter()


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department_in: DepartmentCreate,
    db: AsyncSession = Depends(deps.get_async_db),
    current_user: UserSchema = Depends(RequirePermission(DepartmentPermissions.CREATE)),
):
    """Create a new department."""
    department = await department_service.create_department(
        db=db, department_in=department_in, organization_id=current_user.organizationId
    )
    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department could not be created.",
        )
    return department


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_async_db),
    current_user: UserSchema = Depends(RequirePermission(DepartmentPermissions.READ)),
):
    """Get a specific department by its ID."""
    department = await department_service.get_department_by_id(
        db=db, department_id=department_id, organization_id=current_user.organizationId
    )
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found."
        )
    return department


@router.get("/", response_model=List[DepartmentResponse])
async def list_departments(
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserSchema = Depends(RequirePermission(DepartmentPermissions.LIST)),
):
    """List departments for the user's organization."""
    organization_id = current_user.organizationId
    departments = await department_service.get_departments_by_organization(
        db=db, organization_id=organization_id, skip=skip, limit=limit
    )
    return departments


@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: uuid.UUID,
    department_in: DepartmentUpdate,
    db: AsyncSession = Depends(deps.get_async_db),
    current_user: UserSchema = Depends(RequirePermission(DepartmentPermissions.UPDATE)),
):
    """Update an existing department."""
    existing_department = await department_service.get_department_by_id(
        db=db, department_id=department_id, organization_id=current_user.organizationId
    )
    if not existing_department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found."
        )

    department = await department_service.update_department(
        db=db,
        department_id=department_id,
        department_in=department_in,
        organization_id=current_user.organizationId,
    )
    return department


@router.delete("/{department_id}", response_model=DepartmentResponse)
async def delete_department(
    department_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_async_db),
    current_user: UserSchema = Depends(RequirePermission(DepartmentPermissions.DELETE)),
):
    """Delete a department."""
    department = await department_service.get_department_by_id(
        db=db, department_id=department_id, organization_id=current_user.organizationId
    )
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found."
        )

    deleted_department = await department_service.delete_department(
        db=db, department_id=department_id, organization_id=current_user.organizationId
    )
    return deleted_department
