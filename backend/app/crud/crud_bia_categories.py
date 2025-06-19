from typing import Any, Dict, Optional, Union, List
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.crud.base import CRUDBase
from app.models.domain.bia_categories import BIACategory
from app.schemas.bia_categories import BIACategoryCreate, BIACategoryUpdate


class CRUDBIACategory(CRUDBase[BIACategory, BIACategoryCreate, BIACategoryUpdate]):
    async def get_by_name_and_organization(
        self, db: AsyncSession, *, name: str, organization_id: uuid.UUID
    ) -> Optional[BIACategory]:
        result = await db.execute(
            select(BIACategory)
            .filter(func.lower(BIACategory.name) == func.lower(name))
            .filter(BIACategory.organization_id == organization_id)
            .filter(BIACategory.is_active == True)  # noqa E712
        )
        return result.scalars().first()

    async def create(self, db: AsyncSession, *, obj_in: BIACategoryCreate, organization_id: uuid.UUID, created_by_id: uuid.UUID) -> BIACategory:
        db_obj = BIACategory(
            name=obj_in.name,
            description=obj_in.description,
            organization_id=organization_id,
            created_by_id=created_by_id,
            updated_by_id=created_by_id,  # Set updated_by_id to the creator on creation
            is_active=True
        )
        logger = logging.getLogger(__name__)
        logger.info(f"CRUDBIACategory.create: Attempting to add BIACategory with name='{db_obj.name}', org_id='{db_obj.organization_id}', created_by_id='{db_obj.created_by_id}', updated_by_id='{db_obj.updated_by_id}'")
        db.add(db_obj)
        try:
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A BIA category with this name already exists in the organization.",
            )

    async def get_multi_by_organization(
        self, db: AsyncSession, *, organization_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[BIACategory]:
        result = await db.execute(
            select(self.model)
            .filter(BIACategory.organization_id == organization_id, BIACategory.is_active == True)  # noqa E712
            .order_by(self.model.name)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(
        self, db: AsyncSession, *, db_obj: BIACategory, obj_in: Union[BIACategoryUpdate, Dict[str, Any]]
    ) -> BIACategory:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    async def soft_delete(self, db: AsyncSession, *, id: uuid.UUID, organization_id: uuid.UUID) -> Optional[BIACategory]:
        # Ensure that the object being soft-deleted belongs to the specified organization_id for security.
        result = await db.execute(
            select(self.model).filter(self.model.id == id, self.model.organization_id == organization_id)
        )
        db_obj = result.scalars().first()
        if not db_obj or not db_obj.is_active: # If not found or already inactive
            return None
        
        # If found and active, then proceed to soft delete
        db_obj.is_active = False
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

bia_category = CRUDBIACategory(BIACategory)
