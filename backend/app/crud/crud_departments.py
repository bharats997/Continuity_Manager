import uuid
from typing import Any, Dict, Optional, Union, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.domain.departments import Department # Corrected model import path
from app.schemas.departments import DepartmentCreate, DepartmentUpdate

class CRUDDepartment:
    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Department]:
        result = await db.execute(
            select(Department).options(selectinload(Department.organization)).filter(Department.id == id)
        )
        return result.scalars().first()

    async def get_by_name_and_organization(
        self, db: AsyncSession, *, name: str, organization_id: uuid.UUID
    ) -> Optional[Department]:
        result = await db.execute(
            select(Department)
            .options(selectinload(Department.organization))
            .filter(Department.name == name, Department.organization_id == organization_id)
        )
        return result.scalars().first()

    async def get_multi_by_organization(
        self, db: AsyncSession, *, organization_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Department]:
        result = await db.execute(
            select(Department)
            .options(selectinload(Department.organization))
            .filter(Department.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: DepartmentCreate) -> Department:
        db_obj = Department(
            name=obj_in.name,
            description=obj_in.description,
            organization_id=obj_in.organization_id,
            # manager_id=obj_in.manager_id, # If you have a manager relationship
            is_active=True
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: Department, obj_in: Union[DepartmentUpdate, Dict[str, Any]]
    ) -> Department:
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

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Department]:
        # Consider soft delete (e.g., set is_active=False) vs hard delete
        obj = await self.get(db, id=id)
        if obj:
            # For soft delete:
            obj.is_active = False
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
            # For hard delete:
            # await db.delete(obj)
            # await db.commit()
            # return obj
        return None

department = CRUDDepartment()
