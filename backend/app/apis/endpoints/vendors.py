import uuid
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.models.domain.users import User as UserModel # Domain model for user
from ...schemas.user_schemas import UserSchema as User # Pydantic model for user, includes roles
from app.models.vendor import VendorCreate, VendorUpdate, VendorResponse
from app.services.vendor_service import VendorService
from app.utils.rbac import get_current_active_user_with_roles, ensure_user_has_roles # Assuming this exists
from app.utils.common_schemas import PaginationResponse
from ...schemas.role import RoleName # Assuming RoleName enum exists
from app.utils.exceptions import ConflictException # Import ConflictException

router = APIRouter()

# Role definitions for access control
ADMIN_ROLES = [RoleName.ADMIN, RoleName.SUPER_ADMIN]
READ_ROLES = [RoleName.ADMIN, RoleName.SUPER_ADMIN, RoleName.BCM_MANAGER, RoleName.CISO]

@router.post(
    "/", 
    response_model=VendorResponse, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(ensure_user_has_roles(ADMIN_ROLES))]
)
async def create_vendor(
    vendor_in: VendorCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_active_user_with_roles)
) -> VendorResponse:
    """
    Create a new vendor. Requires Admin privileges.
    """
    vendor_service = VendorService(db)
    try:
        created_vendor = await vendor_service.create_vendor(
            vendor_data=vendor_in, 
            current_user_id=current_user.id, 
            organization_id=current_user.organization_id
        )
        return VendorResponse.model_validate(created_vendor)
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        # Catch other specific exceptions from service if needed
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get(
    "/", 
    response_model=PaginationResponse[VendorResponse],
    dependencies=[Depends(ensure_user_has_roles(READ_ROLES))]
)
async def list_vendors(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of items to return"),
    sort_by: Optional[str] = Query(None, description="Field to sort by (e.g., 'name')"),
    sort_order: Optional[str] = Query("asc", description="Sort order ('asc' or 'desc')"),
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_active_user_with_roles)
) -> PaginationResponse[VendorResponse]:
    """
    List all vendors for the organization. Accessible by Admin, BCM Manager, CISO.
    """
    vendor_service = VendorService(db)
    vendors = await vendor_service.get_all_vendors(
        organization_id=current_user.organization_id, 
        skip=skip, 
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    total_vendors = await vendor_service.count_vendors(organization_id=current_user.organization_id)
    
    return PaginationResponse(
        total_items=total_vendors,
        items=[VendorResponse.model_validate(vendor) for vendor in vendors],
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get(
    "/{vendor_id}", 
    response_model=VendorResponse,
    dependencies=[Depends(ensure_user_has_roles(READ_ROLES))]
)
async def get_vendor(
    vendor_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_active_user_with_roles)
) -> VendorResponse:
    """
    Get a specific vendor by ID. Accessible by Admin, BCM Manager, CISO.
    """
    vendor_service = VendorService(db)
    vendor = await vendor_service.get_vendor_by_id(vendor_id, current_user.organization_id)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return VendorResponse.model_validate(vendor)

@router.put(
    "/{vendor_id}", 
    response_model=VendorResponse,
    dependencies=[Depends(ensure_user_has_roles(ADMIN_ROLES))]
)
async def update_vendor(
    vendor_id: uuid.UUID,
    vendor_in: VendorUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_active_user_with_roles)
) -> VendorResponse:
    """
    Update an existing vendor. Requires Admin privileges.
    """
    vendor_service = VendorService(db)
    try:
        updated_vendor = await vendor_service.update_vendor(
            vendor_id=vendor_id, 
            vendor_data=vendor_in, 
            current_user_id=current_user.id, 
            organization_id=current_user.organization_id
        )
        if not updated_vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found or cannot be updated")
        return VendorResponse.model_validate(updated_vendor)
    except Exception as e:
        # Catch specific exceptions (NotFound, Conflict, UnprocessableEntity)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete(
    "/{vendor_id}", 
    response_model=VendorResponse, # Or perhaps a status message
    dependencies=[Depends(ensure_user_has_roles(ADMIN_ROLES))]
)
async def delete_vendor(
    vendor_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_active_user_with_roles)
) -> VendorResponse:
    """
    Soft delete a vendor (mark as inactive). Requires Admin privileges.
    """
    vendor_service = VendorService(db)
    deleted_vendor = await vendor_service.delete_vendor(
        vendor_id=vendor_id, 
        current_user_id=current_user.id, 
        organization_id=current_user.organization_id
    )
    if not deleted_vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return VendorResponse.model_validate(deleted_vendor)
