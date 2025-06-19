"""
API Endpoints for BIA Impact Criteria
"""
from typing import List, Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis import deps # Corrected import path for deps
from app.utils.rbac import ensure_user_has_permissions # Import for permission checking

from app.models.domain.users import User 
from app.schemas.bia_impact_criteria import (
    BIAImpactCriterion,
    BIAImpactCriterionCreate,
    BIAImpactCriterionUpdate,
    PaginatedBIAImpactCriteria
)
from app.services.bia_impact_criteria_service import BIAImpactCriteriaService
from app.core.exceptions import NotFoundException, BadRequestException

router = APIRouter()

# Define Permission Constants
CREATE_BIA_IMPACT_CRITERION_PERMISSION = "bia_impact_criterion:create"
READ_BIA_IMPACT_CRITERION_PERMISSION = "bia_impact_criterion:read"
UPDATE_BIA_IMPACT_CRITERION_PERMISSION = "bia_impact_criterion:update"
DELETE_BIA_IMPACT_CRITERION_PERMISSION = "bia_impact_criterion:delete"

# Dependency to get the service
def get_bia_impact_criteria_service(db_session: AsyncSession = Depends(deps.get_async_db)) -> BIAImpactCriteriaService:
    return BIAImpactCriteriaService(db_session)

@router.post(
    "/",
    response_model=BIAImpactCriterion,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new BIA Impact Criterion with its levels",
    dependencies=[Depends(ensure_user_has_permissions([CREATE_BIA_IMPACT_CRITERION_PERMISSION]))]
)
async def create_bia_impact_criterion(
    *, 
    criterion_in: BIAImpactCriterionCreate, 
    service: BIAImpactCriteriaService = Depends(get_bia_impact_criteria_service),
    current_user: User = Depends(deps.get_current_active_user)
) -> BIAImpactCriterion:
    """
    Create a new BIA Impact Criterion along with its associated rating levels.

    - **parameter_name**: Name of the impact parameter (e.g., Financial Loss, Reputational Damage).
    - **description**: Optional description of the parameter.
    - **rating_type**: 'QUALITATIVE' or 'QUANTITATIVE'.
    - **bia_category_id**: UUID of the BIA Category this criterion belongs to.
    - **levels**: A list of BIA Impact Criterion Levels to be created.
    """
    try:
        if not current_user.organization_id:
             raise BadRequestException(detail="User is not associated with an organization.")
        
        created_criterion = await service.create_criterion_with_levels(
            obj_in=criterion_in, 
            organization_id=current_user.organization_id, 
            created_by_id=current_user.id
        )
        return created_criterion
    except BadRequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # In a production app, you'd log the error `e`
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the BIA impact criterion.")

@router.get(
    "/{criterion_id}", 
    response_model=BIAImpactCriterion,
    summary="Get a BIA Impact Criterion by ID",
    dependencies=[Depends(ensure_user_has_permissions([READ_BIA_IMPACT_CRITERION_PERMISSION]))]
)
async def get_bia_impact_criterion(
    criterion_id: UUID, 
    service: BIAImpactCriteriaService = Depends(get_bia_impact_criteria_service),
    current_user: User = Depends(deps.get_current_active_user)
) -> BIAImpactCriterion:
    """
    Retrieve a specific BIA Impact Criterion by its ID.
    """
    if not current_user.organization_id:
        raise BadRequestException(detail="User is not associated with an organization.")

    criterion = await service.get_criterion_by_id(criterion_id=criterion_id, organization_id=current_user.organization_id)
    if not criterion:
        raise NotFoundException(detail=f"BIA Impact Criterion with ID {criterion_id} not found.")
    return criterion

@router.get(
    "/", 
    response_model=PaginatedBIAImpactCriteria,
    summary="Get all BIA Impact Criteria for the organization",
    dependencies=[Depends(ensure_user_has_permissions([READ_BIA_IMPACT_CRITERION_PERMISSION]))]
)
async def get_all_bia_impact_criteria(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    service: BIAImpactCriteriaService = Depends(get_bia_impact_criteria_service),
    current_user: User = Depends(deps.get_current_active_user)
) -> PaginatedBIAImpactCriteria:
    """
    Retrieve all BIA Impact Criteria for the current user's organization, with pagination.
    """
    if not current_user.organization_id:
        raise BadRequestException(detail="User is not associated with an organization.")

    criteria_data = await service.get_criteria_by_organization(
        organization_id=current_user.organization_id, page=page, size=size
    )
    return PaginatedBIAImpactCriteria(**criteria_data)

@router.put(
    "/{criterion_id}", 
    response_model=BIAImpactCriterion,
    summary="Update a BIA Impact Criterion",
    dependencies=[Depends(ensure_user_has_permissions([UPDATE_BIA_IMPACT_CRITERION_PERMISSION]))]
)
async def update_bia_impact_criterion(
    criterion_id: UUID, 
    criterion_in: BIAImpactCriterionUpdate, 
    service: BIAImpactCriteriaService = Depends(get_bia_impact_criteria_service),
    current_user: User = Depends(deps.get_current_active_user)
) -> BIAImpactCriterion:
    """
    Update an existing BIA Impact Criterion and its levels.
    If levels are provided in the input, existing levels will be replaced.
    """
    if not current_user.organization_id:
        raise BadRequestException(detail="User is not associated with an organization.")

    updated_criterion = await service.update_criterion_with_levels(
        criterion_id=criterion_id, 
        obj_in=criterion_in, 
        organization_id=current_user.organization_id, 
        updated_by_id=current_user.id
    )
    if not updated_criterion:
        raise NotFoundException(detail=f"BIA Impact Criterion with ID {criterion_id} not found or update failed.")
    return updated_criterion

@router.delete(
    "/{criterion_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a BIA Impact Criterion",
    dependencies=[Depends(ensure_user_has_permissions([DELETE_BIA_IMPACT_CRITERION_PERMISSION]))]
)
async def delete_bia_impact_criterion(
    criterion_id: UUID, 
    service: BIAImpactCriteriaService = Depends(get_bia_impact_criteria_service),
    current_user: User = Depends(deps.get_current_active_user)
) -> None:
    """
    Delete a BIA Impact Criterion by its ID.
    """
    if not current_user.organization_id:
        raise BadRequestException(detail="User is not associated with an organization.")
        
    deleted_criterion = await service.delete_criterion(criterion_id=criterion_id, organization_id=current_user.organization_id)
    if not deleted_criterion:
        raise NotFoundException(detail=f"BIA Impact Criterion with ID {criterion_id} not found.")
    return None
