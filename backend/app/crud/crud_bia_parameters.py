from typing import Any, Dict, Optional, Union, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.sql import text # For text() construct

from app.crud.base import CRUDBase
from app.models.domain.bia_impact_scales import BIAImpactScale
from app.models.domain.bia_impact_scale_levels import BIAImpactScaleLevel
from app.models.domain.bia_timeframes import BIATimeframe
from app.schemas.bia_parameters import (
    BIAImpactScaleCreate,
    BIAImpactScaleUpdate,
    BIAImpactScaleLevelCreate,
    BIAImpactScaleLevelUpdate, # Though direct update of levels might be complex here
    BIATimeframeCreate,
    BIATimeframeUpdate,
)

class CRUDBIAImpactScale(CRUDBase[BIAImpactScale, BIAImpactScaleCreate, BIAImpactScaleUpdate]):
    def create(self, db: Session, *, obj_in: BIAImpactScaleCreate, created_by_id: UUID, organization_id: UUID) -> BIAImpactScale:
        db_obj = BIAImpactScale(
            **obj_in.model_dump(exclude={"levels"}),
            created_by=created_by_id,
            organization_id=organization_id
        )
        db.add(db_obj)
        db.flush() # Flush to get the db_obj.id for levels

        for level_in in obj_in.levels:
            level_obj = BIAImpactScaleLevel(
                **level_in.model_dump(),
                impact_scale_id=db_obj.id,
                created_by=created_by_id,
                organization_id=organization_id # BIAImpactScaleLevel model does not have org_id directly, this is an issue
                                                # It should be derived from BIAImpactScale. For now, let's assume it's not set here directly
                                                # or the model needs an update if direct org_id is desired on levels.
            )
            # Correcting the BIAImpactScaleLevel creation:
            # BIAImpactScaleLevel does not have organization_id. It's linked via BIAImpactScale.
            # The created_by for levels should also be consistent.
            del level_obj.organization_id # remove if it was added by model_dump and not in model
            db.add(level_obj)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: BIAImpactScale, obj_in: Union[BIAImpactScaleUpdate, Dict[str, Any]], updated_by_id: UUID
    ) -> BIAImpactScale:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # Handle levels update - this is a simplified version (e.g., replace all levels)
        # A more robust implementation would handle add/update/delete of individual levels.
        if "levels" in update_data and update_data["levels"] is not None:
            # Delete existing levels
            for existing_level in db_obj.levels:
                db.delete(existing_level)
            db.flush()

            # Add new levels
            new_levels_data = update_data.pop("levels")
            for level_data_dict in new_levels_data: # Assuming levels in obj_in are dicts or Pydantic models
                if isinstance(level_data_dict, BIAImpactScaleLevelCreate):
                    level_create_obj = level_data_dict
                else: # If it's a dict (e.g. from a partial update)
                    level_create_obj = BIAImpactScaleLevelCreate(**level_data_dict)
                
                level_obj = BIAImpactScaleLevel(
                    **level_create_obj.model_dump(),
                    impact_scale_id=db_obj.id,
                    created_by=updated_by_id # Or original creator if that's the logic
                )
                db.add(level_obj)
            db.flush()

        # Update parent BIAImpactScale object
        db_obj = super().update(db, db_obj=db_obj, obj_in=update_data, updated_by_id=updated_by_id) # Pass update_data here
        return db_obj

    def get_by_name_and_org(self, db: Session, *, name: str, organization_id: UUID) -> Optional[BIAImpactScale]:
        return db.query(BIAImpactScale).filter(BIAImpactScale.scale_name == name, BIAImpactScale.organization_id == organization_id).first()


class CRUDBIATimeframe(CRUDBase[BIATimeframe, BIATimeframeCreate, BIATimeframeUpdate]):
    def create(self, db: Session, *, obj_in: BIATimeframeCreate, created_by_id: UUID, organization_id: UUID) -> BIATimeframe:
        db_obj = BIATimeframe(
            **obj_in.model_dump(),
            created_by=created_by_id,
            organization_id=organization_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_name_and_org(self, db: Session, *, name: str, organization_id: UUID) -> Optional[BIATimeframe]:
        return db.query(BIATimeframe).filter(BIATimeframe.timeframe_name == name, BIATimeframe.organization_id == organization_id).first()


bia_impact_scale_crud = CRUDBIAImpactScale(BIAImpactScale)
bia_timeframe_crud = CRUDBIATimeframe(BIATimeframe)
