"""
BIA Impact Criteria Service
"""
from typing import List, Optional, Union, Dict, Any
from uuid import UUID
import logging
import sys # For diagnostic printing

from sqlalchemy import select, func # Keep this one for select and func
# from sqlalchemy.future import select # Remove duplicate select, sqlalchemy.future.select is usually for older SQLAlchemy versions or specific use cases not apparent here
from sqlalchemy.orm import joinedload, selectinload, class_mapper # Keep this one for class_mapper
from sqlalchemy.ext.asyncio import AsyncSession 
# from sqlalchemy.orm import class_mapper # Remove duplicate class_mapper
# import sys # Remove duplicate sys

from app.models.domain.bia_impact_criteria import BIAImpactCriterion, BIAImpactCriterionLevel
from app.models.domain.users import User
from app.db.session import Base # For diagnostic comparison
from app.schemas.bia_impact_criteria import (
    BIAImpactCriterionCreate,
    BIAImpactCriterionUpdate,
    BIAImpactCriterionLevelCreate,
    BIAImpactCriterionLevelUpdate
)
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundException, BadRequestException

logger = logging.getLogger(__name__)

class BIAImpactCriteriaService(BaseService[BIAImpactCriterion, BIAImpactCriterionCreate, BIAImpactCriterionUpdate]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(BIAImpactCriterion, db_session)

    async def create_criterion_with_levels(
        self, *, obj_in: BIAImpactCriterionCreate, organization_id: UUID, created_by_id: UUID
    ) -> BIAImpactCriterion:
        """Create a BIA Impact Criterion along with its levels."""
        if not obj_in.levels:
            raise BadRequestException(detail="At least one impact criterion level is required.")

        criterion_data = obj_in.model_dump(exclude={'levels'})

        # --- DIAGNOSTICS FOR BIAImpactCriterion ---
        from sqlalchemy import inspect
        print("--- Service Layer DIAGNOSTICS ---")
        print(f"BIAImpactCriterion class in service: {BIAImpactCriterion}")
        print(f"ID of BIAImpactCriterion class: {id(BIAImpactCriterion)}")
        # Find the Base class in the Method Resolution Order (MRO)
        base_class_in_mro = next((base for base in BIAImpactCriterion.__mro__ if hasattr(base, 'metadata')), None)
        print(f"BIAImpactCriterion MRO: {BIAImpactCriterion.__mro__}")
        print(f"Base class from MRO: {base_class_in_mro}")
        if base_class_in_mro:
            print(f"ID of Base class from MRO: {id(base_class_in_mro)}")
        try:
            mapper = inspect(BIAImpactCriterion)
            print(f"Mapper columns: {list(mapper.columns.keys())}")
        except Exception as e:
            print(f"Could not inspect mapper: {e}")
        print("-----------------------------------")

        db_criterion = BIAImpactCriterion(
            **criterion_data,
            organization_id=organization_id,
            created_by_id=created_by_id,
            updated_by_id=created_by_id
        )
        self.db_session.add(db_criterion)
        await self.db_session.flush() # Flush to get the criterion ID

        for level_in in obj_in.levels:
            db_level = BIAImpactCriterionLevel(
                **level_in.model_dump(),
                bia_impact_criterion_id=db_criterion.id,
                organization_id=organization_id,
                created_by_id=created_by_id,
                updated_by_id=created_by_id
            )
            self.db_session.add(db_level)
        
        await self.db_session.commit()
        await self.db_session.refresh(db_criterion, ['levels', 'created_by', 'updated_by'])
        return db_criterion

    async def get_criterion_by_id(self, criterion_id: UUID, organization_id: UUID) -> Optional[BIAImpactCriterion]:
        """Get a BIA Impact Criterion by ID for a specific organization."""
        stmt = (
            select(self.model)
            .where(self.model.id == criterion_id, self.model.organization_id == organization_id)
            .options(
                selectinload(self.model.levels),
                joinedload(self.model.created_by),
                joinedload(self.model.updated_by)
            )
        )
        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def get_criteria_by_organization(
        self, *, organization_id: UUID, page: int = 1, size: int = 20
    ) -> Dict[str, Any]:
        """Get all BIA Impact Criteria for a specific organization with pagination."""
        offset = (page - 1) * size
        
        # Query for criteria
        stmt_criteria = (
            select(self.model)
            .where(self.model.organization_id == organization_id)
            .order_by(self.model.parameter_name)
            .offset(offset)
            .limit(size)
            .options(
                selectinload(self.model.levels).joinedload(BIAImpactCriterionLevel.created_by),
                selectinload(self.model.levels).joinedload(BIAImpactCriterionLevel.updated_by),
                joinedload(self.model.created_by),
                joinedload(self.model.updated_by)
            )
        )
        result_criteria = await self.db_session.execute(stmt_criteria)
        criteria = result_criteria.scalars().all()

        # Query for total count
        stmt_total = (
            select(func.count(self.model.id))
            .where(self.model.organization_id == organization_id)
        )
        total_result = await self.db_session.execute(stmt_total)
        total = total_result.scalar_one_or_none() or 0

        return {"total": total, "page": page, "size": size, "results": criteria}

    async def update_criterion_with_levels(
        self, *, criterion_id: UUID, obj_in: BIAImpactCriterionUpdate, organization_id: UUID, updated_by_id: UUID
    ) -> Optional[BIAImpactCriterion]:
        """Update a BIA Impact Criterion, including its levels."""
        db_criterion = await self.get_criterion_by_id(criterion_id=criterion_id, organization_id=organization_id)
        if not db_criterion:
            return None

        update_data = obj_in.model_dump(exclude_unset=True, exclude={'levels'})
        for field, value in update_data.items():
            setattr(db_criterion, field, value)
        db_criterion.updated_by_id = updated_by_id

        if obj_in.levels is not None:
            # Simple approach: delete existing levels and create new ones
            # More sophisticated logic could be to match by ID and update/create/delete
            for level in db_criterion.levels:
                await self.db_session.delete(level)
            await self.db_session.flush()
            db_criterion.levels = [] # Clear the collection before adding new ones

            for level_in in obj_in.levels:
                db_level = BIAImpactCriterionLevel(
                    **level_in.model_dump(),
                    bia_impact_criterion_id=db_criterion.id,
                    organization_id=organization_id,
                    created_by_id=updated_by_id, # Assuming new levels are created by current updater
                    updated_by_id=updated_by_id
                )
                db_criterion.levels.append(db_level) # Add to session via relationship
        
        self.db_session.add(db_criterion)
        await self.db_session.commit()
        await self.db_session.refresh(db_criterion, ['levels', 'created_by', 'updated_by'])
        return db_criterion

    async def delete_criterion(self, *, criterion_id: UUID, organization_id: UUID) -> Optional[BIAImpactCriterion]:
        """Delete a BIA Impact Criterion by ID for a specific organization."""
        db_criterion = await self.get_criterion_by_id(criterion_id=criterion_id, organization_id=organization_id)
        if not db_criterion:
            return None
        
        await self.db_session.delete(db_criterion)
        await self.db_session.commit()
        return db_criterion
