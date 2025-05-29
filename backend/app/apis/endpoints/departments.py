# backend/app/apis/endpoints/departments.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ... import models # Assuming Pydantic models are in backend/app/models/
from ...services import department_service # Assuming service is in backend/app/services/
from .. import deps # For get_db and RBAC

router = APIRouter()

@router.post("/", response_model=models.department.DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department_in: models.department.DepartmentCreate,
    db: Session = Depends(deps.get_db),
    # current_user: models.domain.people.Person = Depends(deps.allow_department_management) # RBAC
):
    """
    Create a new department.
    (Requires 'Admin' or 'BCM Manager' role - placeholder RBAC)
    """
    # Ensure organizationId is provided or derived from current_user if applicable
    # For now, assuming organizationId is part of department_in or handled by service
    # organization_id = current_user.organizationId
    # department = department_service.create_department(db=db, department_in=department_in, organization_id=organization_id)
    department = department_service.create_department(db=db, department_in=department_in)
    if not department:
        raise HTTPException(status_code=400, detail="Department could not be created.")
    return department

@router.get("/{department_id}", response_model=models.department.DepartmentResponse)
async def get_department(
    department_id: int,
    db: Session = Depends(deps.get_db),
    # current_user: models.domain.people.Person = Depends(deps.get_current_active_user) # Or a more specific read permission
):
    """
    Get a specific department by its ID.
    """
    # organization_id = current_user.organizationId
    # department = department_service.get_department_by_id(db=db, department_id=department_id, organization_id=organization_id)
    department = department_service.get_department_by_id(db=db, department_id=department_id)
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")
    return department

@router.get("/", response_model=List[models.department.DepartmentResponse])
async def list_departments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.domain.people.Person = Depends(deps.get_current_user_placeholder)
):
    """
    List departments for the user's organization.
    """
    organization_id = current_user.organizationId
    departments = department_service.get_departments_by_organization(db=db, organization_id=organization_id, skip=skip, limit=limit)
    # departments = department_service.get_all_departments(db=db, skip=skip, limit=limit) # Simplified for now
    return departments

@router.put("/{department_id}", response_model=models.department.DepartmentResponse)
async def update_department(
    department_id: int,
    department_in: models.department.DepartmentUpdate,
    db: Session = Depends(deps.get_db),
    # current_user: models.domain.people.Person = Depends(deps.allow_department_management)
):
    """
    Update an existing department.
    (Requires 'Admin' or 'BCM Manager' role - placeholder RBAC)
    """
    # organization_id = current_user.organizationId
    # existing_department = department_service.get_department_by_id(db=db, department_id=department_id, organization_id=organization_id)
    existing_department = department_service.get_department_by_id(db=db, department_id=department_id) # Simplified
    if not existing_department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")
    
    # department = department_service.update_department(db=db, department_obj=existing_department, department_in=department_in)
    department = department_service.update_department(db=db, department_id=department_id, department_in=department_in)
    return department

@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: int,
    db: Session = Depends(deps.get_db),
    # current_user: models.domain.people.Person = Depends(deps.allow_department_management)
):
    """
    Delete a department.
    (Requires 'Admin' or 'BCM Manager' role - placeholder RBAC)
    """
    # organization_id = current_user.organizationId
    # department = department_service.get_department_by_id(db=db, department_id=department_id, organization_id=organization_id)
    department = department_service.get_department_by_id(db=db, department_id=department_id) # Simplified
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")
    
    # department_service.delete_department(db=db, department_id=department_id, organization_id=organization_id)
    department_service.delete_department(db=db, department_id=department_id)
    return None
