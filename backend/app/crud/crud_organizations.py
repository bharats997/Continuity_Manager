import uuid
from typing import Any, Dict, Optional, Union, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.domain.organizations import Organization # Assuming model is in app.models.organization
from app.schemas.organizations import OrganizationCreate, OrganizationUpdate

class CRUDOrganization:
    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Organization]:
        result = await db.execute(select(Organization).filter(Organization.id == id))
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Organization]:
        result = await db.execute(select(Organization).filter(Organization.name == name))
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Organization]:
        result = await db.execute(select(Organization).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: OrganizationCreate) -> Organization:
        db_obj = Organization(
            name=obj_in.name,
            description=obj_in.description,
            # industry=obj_in.industry, # If part of your schema/model
            # website=str(obj_in.website) if obj_in.website else None, # If part of your schema/model
            is_active=True # Default to active
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: Organization, obj_in: Union[OrganizationUpdate, Dict[str, Any]]
    ) -> Organization:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) # Pydantic v2

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                # if field == "website" and value is not None:
                #     setattr(db_obj, field, str(value))
                # else:
                setattr(db_obj, field, value)
            
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Organization]:
        # Consider soft delete (e.g., set is_active=False) vs hard delete
        obj = await self.get(db, id=id)
        if obj:
            # For hard delete:
            # await db.delete(obj)
            # await db.commit()
            # return obj
            
            # For soft delete:
            obj.is_active = False
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
        return None

organization = CRUDOrganization()
