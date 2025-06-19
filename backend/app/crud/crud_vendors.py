import uuid
from typing import Any, Dict, Optional, Union, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.domain.vendors import Vendor # Assuming model path
from app.schemas.vendors import VendorCreate, VendorUpdate

class CRUDVendor:
    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Vendor]:
        result = await db.execute(
            select(Vendor).options(selectinload(Vendor.organization)).filter(Vendor.id == id)
        )
        return result.scalars().first()

    async def get_by_name_and_organization(
        self, db: AsyncSession, *, name: str, organization_id: uuid.UUID
    ) -> Optional[Vendor]:
        result = await db.execute(
            select(Vendor)
            .options(selectinload(Vendor.organization))
            .filter(Vendor.name == name, Vendor.organization_id == organization_id)
        )
        return result.scalars().first()

    async def get_multi_by_organization(
        self, db: AsyncSession, *, organization_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Vendor]:
        result = await db.execute(
            select(Vendor)
            .options(selectinload(Vendor.organization))
            .filter(Vendor.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: VendorCreate) -> Vendor:
        db_obj = Vendor(
            name=obj_in.name,
            contact_person=obj_in.contact_person,
            email=obj_in.email,
            phone_number=obj_in.phone_number,
            address=obj_in.address,
            service_type=obj_in.service_type,
            organization_id=obj_in.organization_id,
            is_active=True
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: Vendor, obj_in: Union[VendorUpdate, Dict[str, Any]]
    ) -> Vendor:
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

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Vendor]:
        obj = await self.get(db, id=id)
        if obj:
            obj.is_active = False # Soft delete
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
        return None

vendor = CRUDVendor()
