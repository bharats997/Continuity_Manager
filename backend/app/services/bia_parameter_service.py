from typing import List, Optional
from uuid import UUID
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
import logging

from ..models.domain.bia_impact_scales import BIAImpactScale
from ..models.domain.bia_impact_scale_levels import BIAImpactScaleLevel
from ..models.domain.bia_timeframes import BIATimeframe
from ..schemas import bia_parameters as schemas
from ..utils.exceptions import NotFoundError, BadRequestError, InternalServerError

logger = logging.getLogger(__name__)

# Common eager loading options for BIAImpactScale to ensure all related data for responses is loaded.
_bia_impact_scale_load_options = [
    selectinload(BIAImpactScale.organization),
    selectinload(BIAImpactScale.created_by),  # Assuming UserAuditInfo is simple
    selectinload(BIAImpactScale.updated_by),  # Assuming UserAuditInfo is simple
    selectinload(BIAImpactScale.levels).selectinload(BIAImpactScaleLevel.created_by), # Assuming UserAuditInfo is simple
    selectinload(BIAImpactScale.levels).selectinload(BIAImpactScaleLevel.updated_by)  # Assuming UserAuditInfo is simple
]

# Common eager loading options for BIATimeframe
_bia_timeframe_load_options = [
    selectinload(BIATimeframe.organization),
    selectinload(BIATimeframe.created_by),  # Assuming UserAuditInfo is simple
    selectinload(BIATimeframe.updated_by)   # Assuming UserAuditInfo is simple
]

# BIA Impact Scale Service Functions
async def create_impact_scale(
    db: AsyncSession, scale_in: schemas.BIAImpactScaleCreate, user_id: UUID, organization_id: UUID
) -> BIAImpactScale:
    logger.info(f"SERVICE create_impact_scale: Entering. scale_in: {scale_in.model_dump_json(indent=2)}, user_id: {user_id}, org_id: {organization_id}")

    # Check for existing active scale with the same name in the organization
    stmt_check_existing = select(BIAImpactScale).where(
        and_(
            BIAImpactScale.organization_id == organization_id,
            func.lower(BIAImpactScale.scale_name) == func.lower(scale_in.scale_name),
            BIAImpactScale.is_active == True
        )
    )
    existing_scale = (await db.execute(stmt_check_existing)).scalars().first()
    if existing_scale:
        raise BadRequestError(f"An active BIA Impact Scale with name '{scale_in.scale_name}' already exists in this organization.")

    # The whole creation process is a single transaction
    try:
        # Create the parent scale object
        db_scale = BIAImpactScale(
            **scale_in.model_dump(exclude={'levels'}),
            organization_id=organization_id,
            created_by_id=user_id,
            updated_by_id=user_id
        )
        # Manually set timestamps
        current_utc_time = datetime.datetime.utcnow()
        db_scale.created_at = current_utc_time
        db_scale.updated_at = current_utc_time
        db.add(db_scale)
        logger.info(f"SERVICE create_impact_scale: BIAImpactScale object '{db_scale.scale_name}' created and added to session.")

        # Flush to get the parent ID for the children, but don't commit yet
        await db.flush()
        logger.info(f"SERVICE create_impact_scale: db.flush() successful. db_scale.id: {db_scale.id}")

        # Create and add child level objects
        for level_in in scale_in.levels:
            db_level = BIAImpactScaleLevel(
                **level_in.model_dump(),
                created_by_id=user_id,
                updated_by_id=user_id,
                impact_scale_id=db_scale.id  # Use the flushed ID
            )
            db.add(db_level)
            logger.info(f"SERVICE create_impact_scale: Added level '{db_level.level_name}' to session for scale ID {db_scale.id}")

        # The session will be committed by the caller.
        # Re-fetch to load all relationships for the response model.
        scale_id = db_scale.id
        logger.info(f"SERVICE create_impact_scale: Re-fetching scale ID {scale_id} with all relationships.")
        stmt_refetch = (
            select(BIAImpactScale)
            .where(BIAImpactScale.id == scale_id)
            .options(*_bia_impact_scale_load_options)
        )
        result = await db.execute(stmt_refetch)
        refetched_scale = result.scalars().one_or_none()
        if refetched_scale is None:
            logger.error(f"SERVICE create_impact_scale: Failed to re-fetch scale ID {scale_id} after flush. This indicates a potential issue with data visibility within the transaction.")
            raise InternalServerError("Failed to retrieve impact scale after creation due to an internal data visibility issue.")
        logger.info(f"SERVICE create_impact_scale: Re-fetch successful. Returning scale ID {refetched_scale.id}")
        return refetched_scale

    except IntegrityError as e:
        # Rollback will be handled by the caller (e.g., test fixture or API dependency)
        logger.error(f"SERVICE create_impact_scale: IntegrityError occurred: {e.orig}", exc_info=True)
        # Provide more specific error messages based on constraint violations
        if e.orig and 'uq_organization_scale_name' in str(e.orig):
             raise BadRequestError(f"BIA Impact Scale name '{scale_in.scale_name}' already exists.")
        if e.orig and ('uq_scale_level_value' in str(e.orig) or 'uq_scale_level_name' in str(e.orig)):
            raise BadRequestError("Duplicate level value or name within the same impact scale.")
        raise InternalServerError("A database integrity error occurred while creating the impact scale.") from e
    except Exception as e:
        # Rollback will be handled by the caller (e.g., test fixture or API dependency)
        logger.error(f"SERVICE create_impact_scale: An unexpected error occurred: {e}", exc_info=True)
        raise InternalServerError("An unexpected error occurred while creating the impact scale.") from e

async def get_impact_scale(
    db: AsyncSession, 
    scale_id: UUID, 
    organization_id: UUID
) -> Optional[BIAImpactScale]:
    """Retrieves a specific BIA Impact Scale by ID, including its levels and related audit info."""
    stmt = (
        select(BIAImpactScale)
        .where(
            BIAImpactScale.id == scale_id,
            BIAImpactScale.organization_id == organization_id,
            BIAImpactScale.is_active == True
        )
        .options(*_bia_impact_scale_load_options)
    )
    result = await db.execute(stmt)
    return result.scalars().one_or_none()

async def get_impact_scales(
    db: AsyncSession, 
    organization_id: UUID, 
    skip: int = 0, 
    limit: int = 100
) -> List[BIAImpactScale]:
    """Retrieves a list of active BIA Impact Scales for an organization, with levels and related audit info."""
    stmt = (
        select(BIAImpactScale)
        .where(BIAImpactScale.organization_id == organization_id, BIAImpactScale.is_active == True)
        .order_by(BIAImpactScale.sequence_order, BIAImpactScale.scale_name)
        .options(*_bia_impact_scale_load_options)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def update_impact_scale(
    db: AsyncSession,
    scale_id: UUID,
    scale_in: schemas.BIAImpactScaleUpdate,
    user_id: UUID,
    organization_id: UUID
) -> Optional[BIAImpactScale]:
    """Updates an existing BIA Impact Scale and its levels."""
    # Fetch the existing scale with all relationships to ensure we have the full object state
    stmt_get = select(BIAImpactScale).where(BIAImpactScale.id == scale_id, BIAImpactScale.organization_id == organization_id).options(*_bia_impact_scale_load_options)
    db_scale = (await db.execute(stmt_get)).scalars().first()

    if not db_scale:
        raise NotFoundError(f"BIA Impact Scale with ID {scale_id} not found in organization {organization_id}.")
    
    if not db_scale.is_active:
        raise BadRequestError(f"Cannot update a deleted BIA Impact Scale with ID {scale_id}.")

    update_data = scale_in.model_dump(exclude_unset=True, exclude={'levels'})

    # Proactive check for duplicate scale_name if it's being changed
    if 'scale_name' in update_data and func.lower(update_data['scale_name']) != func.lower(db_scale.scale_name):
        stmt_check_existing = select(BIAImpactScale).where(
            and_(
                BIAImpactScale.organization_id == organization_id,
                func.lower(BIAImpactScale.scale_name) == func.lower(update_data['scale_name']),
                BIAImpactScale.is_active == True,
                BIAImpactScale.id != scale_id  # Exclude the current scale
            )
        )
        existing_scale = (await db.execute(stmt_check_existing)).scalars().first()
        if existing_scale:
            raise BadRequestError(f"An active BIA Impact Scale with name '{update_data['scale_name']}' already exists in this organization.")
    for key, value in update_data.items():
        setattr(db_scale, key, value)
    db_scale.updated_by_id = user_id
    db_scale.updated_at = datetime.datetime.utcnow()

    if scale_in.levels is not None:
        # The logic here is to perform a full replacement of the levels.
        # The `cascade="all, delete-orphan"` on the relationship ensures that when we
        # clear the list, the old levels are marked for deletion from the database.
        
        # Clear existing levels. When new levels are added and committed,
        # SQLAlchemy's cascade="all, delete-orphan" will handle deleting
        # the old levels and adding the new ones in the correct order.
        db_scale.levels.clear()
        # await db.flush()  # Removed: Let SQLAlchemy manage flush order on commit.

        # Add the new levels from the input payload.
        for level_in in scale_in.levels:
            # We assume the payload for levels contains data to create new level instances.
            if isinstance(level_in, schemas.BIAImpactScaleLevelCreate):
                new_level_db = BIAImpactScaleLevel(
                    **level_in.model_dump(),
                    # organization_id is derived from the parent impact_scale
                    created_by_id=user_id,
                    updated_by_id=user_id,
                    is_active=True # Ensure new levels are active
                    # The 'impact_scale_id' will be automatically populated by SQLAlchemy's
                    # relationship back-population when we append to db_scale.levels.
                )
                db_scale.levels.append(new_level_db)
            # else: handle BIAImpactScaleLevelRead if it's meant for update-or-create

    db.add(db_scale)
    try:
        # The session will be committed by the caller.
        # Flush to ensure operations are sent to DB.
        await db.flush() 
        # Re-fetch the scale with all relationships to ensure the returned object is complete for the response.
        # This is important because db.refresh might not reload all nested User objects for created_by/updated_by.
        scale_id_for_refetch = db_scale.id # db_scale.id should still be valid
        stmt_refetch = select(BIAImpactScale).where(BIAImpactScale.id == scale_id_for_refetch).options(*_bia_impact_scale_load_options)
        refetched_db_scale = (await db.execute(stmt_refetch)).scalars().one_or_none()
        if refetched_db_scale is None:
            logger.error(f"SERVICE update_impact_scale: Failed to re-fetch scale ID {scale_id_for_refetch} after update and flush.")
            raise InternalServerError("Failed to retrieve impact scale after update.")
        db_scale = refetched_db_scale
    except IntegrityError as e:
        # Rollback will be handled by the caller.
        if 'uq_organization_scale_name' in str(e.orig):
             raise BadRequestError(f"BIA Impact Scale name '{scale_in.scale_name}' already exists.")
        if 'uq_scale_level_value' in str(e.orig) or 'uq_scale_level_name' in str(e.orig):
            raise BadRequestError("Duplicate level value or name within the same impact scale.")
        raise BadRequestError(f"Database integrity error: {e.orig}")
    return db_scale

async def delete_impact_scale(
    db: AsyncSession, 
    scale_id: UUID, 
    user_id: UUID, 
    organization_id: UUID
) -> Optional[BIAImpactScale]:
    """Soft deletes a BIA Impact Scale and its associated levels."""
    # Fetch the existing scale with all relationships to ensure levels are loaded for soft deletion
    # Fetch regardless of is_active status initially to correctly handle already deleted items.
    stmt_get = (
        select(BIAImpactScale)
        .where(BIAImpactScale.id == scale_id, BIAImpactScale.organization_id == organization_id)
        .options(*_bia_impact_scale_load_options)
    )
    db_scale = (await db.execute(stmt_get)).scalars().first()

    if not db_scale:
        raise NotFoundError(f"BIA Impact Scale with ID {scale_id} not found in organization {organization_id}.")

    if not db_scale.is_active:
        # Already deleted, perhaps return it as is or raise a specific status/error
        logger.info(f"SERVICE delete_impact_scale: Scale ID {scale_id} is already inactive.")
        # Return the already inactive scale, ensuring it's fully loaded as per _bia_impact_scale_load_options.
        return db_scale

    db_scale.is_active = False
    db_scale.updated_by_id = user_id
    db_scale.updated_at = datetime.datetime.utcnow()
    db_scale.is_deleted = True # Explicitly mark as deleted
    db_scale.deleted_at = datetime.datetime.utcnow() # Set deletion timestamp

    for level in db_scale.levels:
        if level.is_active: # Only modify levels that are currently active
            level.is_active = False
            level.is_deleted = True # Explicitly mark as deleted
            level.deleted_at = datetime.datetime.utcnow() # Set deletion timestamp
            level.updated_by_id = user_id
            level.updated_at = datetime.datetime.utcnow()
            db.add(level) # Ensure changes to levels are staged
    
    db.add(db_scale)
    # The session will be committed by the caller.
    # Flush to ensure operations are sent to DB before potential refresh.
    await db.flush()
    # Re-fetch the scale with all relationships to ensure the returned object is complete for the response.
    scale_id_for_refetch = db_scale.id
    stmt_refetch = select(BIAImpactScale).where(BIAImpactScale.id == scale_id_for_refetch).options(*_bia_impact_scale_load_options)
    refetched_db_scale = (await db.execute(stmt_refetch)).scalars().one_or_none()
    # It might be None if the query for get_impact_scale implicitly filters out is_active=False items after this operation
    # For a delete operation, returning the state *before* it's fully filtered by subsequent GETs is often fine.
    # Or, adjust the _bia_impact_scale_load_options or the query here if a fully loaded inactive object is strictly needed.
    # For now, we return the object as it is after flush, or the refetched one if available.
    return refetched_db_scale if refetched_db_scale else db_scale

# BIA Timeframe Service Functions
async def create_timeframe(
    db: AsyncSession,
    timeframe_in: schemas.BIATimeframeCreate,
    user_id: UUID,
    organization_id: UUID
) -> BIATimeframe:
    """Creates a new BIA Timeframe."""
    # Check for existing timeframe with the same name
    stmt_check = select(BIATimeframe).where(
        BIATimeframe.timeframe_name == timeframe_in.timeframe_name,
        BIATimeframe.organization_id == organization_id,
        BIATimeframe.is_active == True
    )
    existing_timeframe = (await db.execute(stmt_check)).scalars().first()
    if existing_timeframe:
        raise BadRequestError(f"An active BIA Timeframe with name '{timeframe_in.timeframe_name}' already exists.")

    db_timeframe = BIATimeframe(
        **timeframe_in.model_dump(),
        organization_id=organization_id,
        created_by_id=user_id,
        updated_by_id=user_id
    )
    db.add(db_timeframe)
    try:
        # Flush to populate the ID, commit will be handled by the caller.
        await db.flush()
        timeframe_id = db_timeframe.id

        # Re-fetch with all relevant relationships loaded for the response
        stmt = (
            select(BIATimeframe)
            .where(BIATimeframe.id == timeframe_id)
            .options(*_bia_timeframe_load_options)
        )
        result = await db.execute(stmt)
        refetched_timeframe = result.scalars().one_or_none()
        if refetched_timeframe is None:
            logger.error(f"SERVICE create_timeframe: Failed to re-fetch timeframe ID {timeframe_id} after flush. This indicates a potential issue with data visibility within the transaction.")
            raise InternalServerError("Failed to retrieve timeframe after creation due to an internal data visibility issue.")
        return refetched_timeframe
        
    except IntegrityError as e:
        # Rollback will be handled by the caller.
        if 'uq_organization_timeframe_name' in str(e.orig):
            raise BadRequestError(f"BIA Timeframe name '{timeframe_in.timeframe_name}' already exists.")
        raise BadRequestError(f"Database integrity error: {e.orig}")

async def get_timeframe(
    db: AsyncSession, 
    timeframe_id: UUID, 
    organization_id: UUID
) -> Optional[BIATimeframe]:
    """Retrieves a specific BIA Timeframe by ID with related audit info."""
    stmt = (
        select(BIATimeframe)
        .where(
            BIATimeframe.id == timeframe_id,
            BIATimeframe.organization_id == organization_id,
            BIATimeframe.is_active == True
        )
        .options(*_bia_timeframe_load_options)
    )
    result = await db.execute(stmt)
    return result.scalars().one_or_none()

async def get_timeframes(
    db: AsyncSession, 
    organization_id: UUID, 
    skip: int = 0, 
    limit: int = 100
) -> List[BIATimeframe]:
    """Retrieves a list of active BIA Timeframes for an organization with related audit info."""
    stmt = (
        select(BIATimeframe)
        .where(BIATimeframe.organization_id == organization_id, 
               BIATimeframe.is_active == True)
        .order_by(BIATimeframe.sequence_order, BIATimeframe.timeframe_name)
        .options(*_bia_timeframe_load_options)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def update_timeframe(
    db: AsyncSession,
    timeframe_id: UUID,
    timeframe_in: schemas.BIATimeframeUpdate,
    user_id: UUID,
    organization_id: UUID
) -> Optional[BIATimeframe]:
    """Updates an existing BIA Timeframe."""
    db_timeframe = await get_timeframe(db, timeframe_id, organization_id)
    if not db_timeframe:
        return None

    update_data = timeframe_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_timeframe, key, value)
    db_timeframe.updated_by_id = user_id
    db_timeframe.updated_at = datetime.datetime.utcnow()
    
    db.add(db_timeframe)
    try:
        # The session will be committed by the caller.
        # Flush to ensure operations are sent to DB before potential refresh.
        await db.flush()
        await db.refresh(db_timeframe)
    except IntegrityError as e:
        # Rollback will be handled by the caller.
        if 'uq_organization_timeframe_name' in str(e.orig) and 'timeframe_name' in update_data:
            raise BadRequestError(f"BIA Timeframe name '{update_data['timeframe_name']}' already exists.")
        raise BadRequestError(f"Database integrity error: {e.orig}")
    return db_timeframe

async def delete_timeframe(
    db: AsyncSession, 
    timeframe_id: UUID, 
    user_id: UUID, 
    organization_id: UUID
) -> Optional[BIATimeframe]:
    """Soft deletes a BIA Timeframe."""
    db_timeframe = await get_timeframe(db, timeframe_id, organization_id)
    if not db_timeframe:
        return None

    db_timeframe.is_active = False
    db_timeframe.updated_by_id = user_id
    db_timeframe.updated_at = datetime.datetime.utcnow()
    
    db.add(db_timeframe)
    # The session will be committed by the caller.
    # Flush to ensure operations are sent to DB before potential refresh.
    await db.flush()
    await db.refresh(db_timeframe)
    return db_timeframe
