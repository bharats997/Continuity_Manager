import uuid
from typing import Any, Dict, Optional, Union, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.domain.locations import Location # Corrected model import path
from app.schemas.locations import LocationCreate, LocationUpdate

class CRUDLocation:
    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Location]:
        result = await db.execute(
            select(Location).options(selectinload(Location.organization)).filter(Location.id == id)
        )
        return result.scalars().first()

    async def get_by_name_and_organization(
        self, db: AsyncSession, *, name: str, organization_id: uuid.UUID
    ) -> Optional[Location]:
        result = await db.execute(
            select(Location)
            .options(selectinload(Location.organization))
            .filter(Location.name == name, Location.organization_id == organization_id)
        )
        return result.scalars().first()

    async def get_multi_by_organization(
        self, db: AsyncSession, *, organization_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Location]:
        result = await db.execute(
            select(Location)
            .options(selectinload(Location.organization))
            .filter(Location.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: LocationCreate) -> Location:
        db_obj = Location(
            name=obj_in.name,
            address_line_1=obj_in.address_line_1,
            address_line_2=obj_in.address_line_2,
            city=obj_in.city,
            state_province_region=obj_in.state_province_region,
            zip_postal_code=obj_in.zip_postal_code,
            country=obj_in.country,
            description=obj_in.description,
            organization_id=obj_in.organization_id,
            is_active=True
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: Location, obj_in: Union[LocationUpdate, Dict[str, Any]]
    ) -> Location:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
            
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Location]:
        obj = await self.get(db, id=id)
        if obj:
            obj.is_active = False
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
        return None

location = CRUDLocation()
