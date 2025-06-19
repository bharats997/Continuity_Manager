import uuid
from typing import Any, Dict, Optional, Union, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Assuming Process model will be in app.models.domain.processes
from app.models.domain.processes import Process 
from app.schemas.processes import ProcessCreate, ProcessUpdate

class CRUDProcess:
    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Process]:
        result = await db.execute(
            select(Process)
            .options(
                selectinload(Process.organization),
                selectinload(Process.department),
                # selectinload(Process.applications), # Many-to-many
                # selectinload(Process.locations) # Many-to-many
            )
            .filter(Process.id == id)
        )
        return result.scalars().first()

    async def get_by_name_and_organization(
        self, db: AsyncSession, *, name: str, organization_id: uuid.UUID
    ) -> Optional[Process]:
        result = await db.execute(
            select(Process)
            .options(selectinload(Process.organization))
            .filter(Process.name == name, Process.organization_id == organization_id)
        )
        return result.scalars().first()

    async def get_multi_by_organization(
        self, db: AsyncSession, *, organization_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Process]:
        result = await db.execute(
            select(Process)
            .options(selectinload(Process.organization))
            .filter(Process.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: ProcessCreate) -> Process:
        # Create Process object without m2m relationships first
        db_obj_data = obj_in.model_dump(exclude={'application_ids', 'location_ids', 'dependency_ids'})
        db_obj = Process(**db_obj_data, is_active=True)
        
        # Handle m2m relationships if IDs are provided
        # This requires Application and Location models to be imported
        # from app.models.domain.applications import Application
        # from app.models.domain.locations import Location
        # from app.models.domain.process_dependencies import ProcessDependency # If you have this model

        # if obj_in.application_ids:
        #     applications = await db.execute(
        #         select(Application).filter(Application.id.in_(obj_in.application_ids))
        #     )
        #     db_obj.applications = applications.scalars().all()

        # if obj_in.location_ids:
        #     locations = await db.execute(
        #         select(Location).filter(Location.id.in_(obj_in.location_ids))
        #     )
        #     db_obj.locations = locations.scalars().all()
        
        # Dependencies might be more complex (e.g., creating ProcessDependency records)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: Process, obj_in: Union[ProcessUpdate, Dict[str, Any]]
    ) -> Process:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # Handle m2m fields separately
        # application_ids = update_data.pop('application_ids', None)
        # location_ids = update_data.pop('location_ids', None)
        # dependency_ids = update_data.pop('dependency_ids', None)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        # if application_ids is not None:
        #     if application_ids:
        #         applications = await db.execute(
        #             select(Application).filter(Application.id.in_(application_ids))
        #         )
        #         db_obj.applications = applications.scalars().all()
        #     else: # Empty list means clear the relationship
        #         db_obj.applications = []

        # Similar handling for location_ids and dependency_ids

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        # Eager load m2m relationships if needed after update
        # await db.refresh(db_obj, attribute_names=['applications', 'locations'])
        return db_obj

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Process]:
        obj = await self.get(db, id=id)
        if obj:
            obj.is_active = False # Soft delete
            # For m2m, SQLAlchemy might handle removal from association tables,
            # or you might need to clear them manually if cascade isn't set up.
            # obj.applications.clear()
            # obj.locations.clear()
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
        return None

process = CRUDProcess()
