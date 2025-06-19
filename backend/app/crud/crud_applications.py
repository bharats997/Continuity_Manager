import uuid
from typing import Any, Dict, Optional, Union, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.domain.applications import Application
from app.models.domain.users import User
from app.schemas.applications import ApplicationCreate, ApplicationUpdate

class CRUDApplication:
    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Application]:
        stmt = (
            select(Application)
            .where(Application.id == id)
            .options(
                selectinload(Application.organization),
                selectinload(Application.app_owner).selectinload(User.roles),
                selectinload(Application.created_by).selectinload(User.roles),
                selectinload(Application.updated_by).selectinload(User.roles),
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_by_name_and_organization(
        self, db: AsyncSession, *, name: str, organization_id: uuid.UUID
    ) -> Optional[Application]:
        stmt = (
            select(Application)
            .where(Application.name == name, Application.organization_id == organization_id)
            .options(
                selectinload(Application.organization),
                selectinload(Application.app_owner).selectinload(User.roles),
                selectinload(Application.created_by).selectinload(User.roles),
                selectinload(Application.updated_by).selectinload(User.roles),
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_multi_by_organization(
        self, db: AsyncSession, *, organization_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Application]:
        stmt = (
            select(Application)
            .where(Application.organization_id == organization_id)
            .options(
                selectinload(Application.organization),
                selectinload(Application.app_owner).selectinload(User.roles),
                selectinload(Application.created_by).selectinload(User.roles),
                selectinload(Application.updated_by).selectinload(User.roles),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: ApplicationCreate) -> Application:
        db_obj = Application(**obj_in.model_dump(), is_active=True)
        db.add(db_obj)
        await db.commit()
        # After commit, the object is expired. Re-fetch it with all relationships loaded.
        return await self.get(db, id=db_obj.id)

    async def update(
        self, db: AsyncSession, *, db_obj: Application, obj_in: Union[ApplicationUpdate, Dict[str, Any]]
    ) -> Application:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        # After commit, the object is expired. Re-fetch it with all relationships loaded.
        return await self.get(db, id=db_obj.id)

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Application]:
        obj = await self.get(db, id=id)
        if obj:
            obj.is_active = False  # Soft delete
            db.add(obj)
            await db.commit()
            # Re-fetch the object to return its updated state with relationships loaded.
            return await self.get(db, id=id)
        return None

application = CRUDApplication()
