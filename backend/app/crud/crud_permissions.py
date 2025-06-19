import uuid
from typing import Any, Dict, Optional, Union, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.domain.permissions import Permission # Adjusted path
from app.schemas.permissions import PermissionCreate, PermissionUpdate

class CRUDPermission:
    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Permission]:
        result = await db.execute(select(Permission).filter(Permission.id == id))
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Permission]:
        result = await db.execute(select(Permission).filter(Permission.name == name))
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Permission]:
        result = await db.execute(select(Permission).offset(skip).limit(limit))
        return result.scalars().all()

    # Permissions are often seeded and not created/updated/deleted frequently via API
    # but including basic CRUD for completeness or admin purposes.
    async def create(self, db: AsyncSession, *, obj_in: PermissionCreate) -> Permission:
        db_obj = Permission(
            name=obj_in.name,
            description=obj_in.description,
            # category=obj_in.category # If category is part of your model/schema
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: Permission, obj_in: Union[PermissionUpdate, Dict[str, Any]]
    ) -> Permission:
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

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Permission]:
        obj = await self.get(db, id=id)
        if obj:
            # Consider checks: e.g., cannot delete permission if it's in use by roles.
            await db.delete(obj)
            await db.commit()
        return obj

permission = CRUDPermission()
