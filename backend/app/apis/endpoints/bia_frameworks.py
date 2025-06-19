import uuid
from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.deps import get_async_db
from app.models.domain.users import User
from app.schemas.role import RoleName
from app.schemas.bia_frameworks import BIAFramework, BIAFrameworkCreate, BIAFrameworkUpdate
from app.services.bia_framework_service import BIAFrameworkService
from app.utils.rbac import ensure_user_has_roles

router = APIRouter()

# Dependency to get the BIAFrameworkService
def get_bia_framework_service(db: AsyncSession = Depends(get_async_db)) -> BIAFrameworkService:
    return BIAFrameworkService(db)

@router.post("/", response_model=BIAFramework, status_code=status.HTTP_201_CREATED)
async def create_bia_framework(
    *, 
    framework_in: BIAFrameworkCreate, 
    service: BIAFrameworkService = Depends(get_bia_framework_service),
    current_user: User = Depends(ensure_user_has_roles([RoleName.BCM_MANAGER, RoleName.CISO]))
) -> BIAFramework:
    """
    Create a new BIA Framework.
    
    **Allowed Roles:** BCM_MANAGER, CISO
    """
    try:
        return await service.create(
            obj_in=framework_in, 
            created_by_id=current_user.id,
            organization_id=current_user.organization_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{framework_id}", response_model=BIAFramework)
async def get_bia_framework(
    framework_id: uuid.UUID,
    service: BIAFrameworkService = Depends(get_bia_framework_service),
    current_user: User = Depends(ensure_user_has_roles([RoleName.BCM_MANAGER, RoleName.CISO, RoleName.DEPARTMENT_MANAGER, RoleName.INTERNAL_AUDITOR]))
) -> BIAFramework:
    """
    Get a BIA Framework by its ID.
    
    **Allowed Roles:** BCM_MANAGER, CISO, PROCESS_OWNER, DEPARTMENT_HEAD, INTERNAL_AUDITOR
    """
    framework = await service.get(id=framework_id)
    if not framework or framework.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BIA Framework not found")
    return framework

@router.put("/{framework_id}", response_model=BIAFramework)
async def update_bia_framework(
    framework_id: uuid.UUID,
    *, 
    framework_in: BIAFrameworkUpdate, 
    service: BIAFrameworkService = Depends(get_bia_framework_service),
    current_user: User = Depends(ensure_user_has_roles([RoleName.BCM_MANAGER, RoleName.CISO]))
) -> BIAFramework:
    """
    Update a BIA Framework.
    
    **Allowed Roles:** BCM_MANAGER, CISO
    """
    db_obj = await service.get(id=framework_id)
    if not db_obj or db_obj.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BIA Framework not found")
    
    try:
        return await service.update(db_obj=db_obj, obj_in=framework_in, updated_by_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{framework_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bia_framework(
    framework_id: uuid.UUID,
    service: BIAFrameworkService = Depends(get_bia_framework_service),
    current_user: User = Depends(ensure_user_has_roles([RoleName.BCM_MANAGER, RoleName.CISO]))
):
    """
    Delete a BIA Framework.
    
    **Allowed Roles:** BCM_MANAGER, CISO
    """
    db_obj = await service.get(id=framework_id)
    if not db_obj or db_obj.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BIA Framework not found")

    await service.remove(id=framework_id)
    return
