from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
import logging

from ..deps import get_async_db
from ...models.domain.users import User
from ...schemas import bia_parameters as schemas
from ...services import bia_parameter_service as service
from ..deps import BIAParameterPermissions, RequirePermission, get_current_active_user
from ...utils.exceptions import NotFoundError, BadRequestError

logger = logging.getLogger(__name__)


# Router for BIA Impact Scales
router_impact_scales = APIRouter(
    tags=["BIA Impact Scales"],
)

# Router for BIA Timeframes
router_timeframes = APIRouter(
    tags=["BIA Timeframes"],
)

# BIA Impact Scale Endpoints
@router_impact_scales.post(
    "/",
    response_model=schemas.BIAImpactScaleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermission(BIAParameterPermissions.CREATE))]
)
async def create_impact_scale(
    scale_in: schemas.BIAImpactScaleCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    logger.info(f"Entering create_impact_scale. User: {current_user.email if current_user else 'NoneUser'}, Org: {current_user.organization_id if current_user else 'NoneOrg'}. Payload: {scale_in.model_dump_json(indent=2) if scale_in else 'NoPayload'}")
    """Create a new BIA Impact Scale, including its levels."""
    try:
        logger.info("Calling service.create_impact_scale")
        result = await service.create_impact_scale(
            db=db, 
            scale_in=scale_in, 
            user_id=current_user.id, 
            organization_id=current_user.organization_id
        )
        logger.info(f"service.create_impact_scale returned successfully. Result ID: {result.id if result else 'NoneResult'}")
        return result
    except BadRequestError as e:
        logger.error(f"BadRequestError in create_impact_scale: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected Exception in create_impact_scale: {str(e)}", exc_info=True)
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

@router_impact_scales.get("/", response_model=List[schemas.BIAImpactScaleRead], dependencies=[Depends(RequirePermission(BIAParameterPermissions.LIST))])
async def list_impact_scales(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all active BIA Impact Scales for the user's organization."""
    return await service.get_impact_scales(
        db=db, 
        organization_id=current_user.organization_id, 
        skip=skip, 
        limit=limit
    )

@router_impact_scales.get("/{scale_id}", response_model=schemas.BIAImpactScaleRead, dependencies=[Depends(RequirePermission(BIAParameterPermissions.READ))])
async def get_impact_scale(
    scale_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific BIA Impact Scale by ID."""
    scale = await service.get_impact_scale(db=db, scale_id=scale_id, organization_id=current_user.organization_id)
    if not scale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BIA Impact Scale not found or not active.")
    return scale

@router_impact_scales.put(
    "/{scale_id}",
    response_model=schemas.BIAImpactScaleRead,
    dependencies=[Depends(RequirePermission(BIAParameterPermissions.UPDATE))]
)
async def update_impact_scale(
    scale_id: UUID,
    scale_in: schemas.BIAImpactScaleUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a BIA Impact Scale. This can include updating its levels."""
    try:
        updated_scale = await service.update_impact_scale(
            db=db, 
            scale_id=scale_id, 
            scale_in=scale_in, 
            user_id=current_user.id, 
            organization_id=current_user.organization_id
        )
        if not updated_scale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BIA Impact Scale not found or not active.")
        return updated_scale
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while updating.")

@router_impact_scales.delete(
    "/{scale_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RequirePermission(BIAParameterPermissions.DELETE))]
)
async def delete_impact_scale(
    scale_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Soft delete a BIA Impact Scale and its levels."""
    deleted_scale = await service.delete_impact_scale(
        db=db, 
        scale_id=scale_id, 
        user_id=current_user.id, 
        organization_id=current_user.organization_id
    )
    if not deleted_scale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BIA Impact Scale not found.")
    # return deleted_scale # Optionally return the object with is_active=False
    return None # For 204 No Content

# BIA Timeframe Endpoints
@router_timeframes.post(
    "/",
    response_model=schemas.BIATimeframeRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermission(BIAParameterPermissions.CREATE))]
)
async def create_timeframe(
    timeframe_in: schemas.BIATimeframeCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new BIA Timeframe."""
    try:
        return await service.create_timeframe(
            db=db, 
            timeframe_in=timeframe_in, 
            user_id=current_user.id, 
            organization_id=current_user.organization_id
        )
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

@router_timeframes.get("/", response_model=List[schemas.BIATimeframeRead], dependencies=[Depends(RequirePermission(BIAParameterPermissions.LIST))])
async def list_timeframes(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all active BIA Timeframes for the user's organization."""
    return await service.get_timeframes(
        db=db, 
        organization_id=current_user.organization_id, 
        skip=skip, 
        limit=limit
    )

@router_timeframes.get("/{timeframe_id}", response_model=schemas.BIATimeframeRead, dependencies=[Depends(RequirePermission(BIAParameterPermissions.READ))])
async def get_timeframe(
    timeframe_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific BIA Timeframe by ID."""
    timeframe = await service.get_timeframe(db=db, timeframe_id=timeframe_id, organization_id=current_user.organization_id)
    if not timeframe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BIA Timeframe not found or not active.")
    return timeframe

@router_timeframes.put(
    "/{timeframe_id}",
    response_model=schemas.BIATimeframeRead,
    dependencies=[Depends(RequirePermission(BIAParameterPermissions.UPDATE))]
)
async def update_timeframe(
    timeframe_id: UUID,
    timeframe_in: schemas.BIATimeframeUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a BIA Timeframe."""
    try:
        updated_timeframe = await service.update_timeframe(
            db=db, 
            timeframe_id=timeframe_id, 
            timeframe_in=timeframe_in, 
            user_id=current_user.id, 
            organization_id=current_user.organization_id
        )
        if not updated_timeframe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BIA Timeframe not found or not active.")
        return updated_timeframe
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while updating.")

@router_timeframes.delete(
    "/{timeframe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RequirePermission(BIAParameterPermissions.DELETE))]
)
async def delete_timeframe(
    timeframe_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Soft delete a BIA Timeframe."""
    deleted_timeframe = await service.delete_timeframe(
        db=db, 
        timeframe_id=timeframe_id, 
        user_id=current_user.id, 
        organization_id=current_user.organization_id
    )
    if not deleted_timeframe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BIA Timeframe not found.")
    return None # For 204 No Content


router = APIRouter()
router.include_router(router_impact_scales, prefix="/impact-scales")
router.include_router(router_timeframes, prefix="/timeframes")

