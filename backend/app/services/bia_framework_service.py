import uuid
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.services.base_service import BaseService
from app.models.domain.bia_frameworks import BIAFramework, BIAFrameworkParameter, BIAFrameworkRTO
from app.schemas.bia_frameworks import BIAFrameworkCreate, BIAFrameworkUpdate

class BIAFrameworkService(BaseService[BIAFramework, BIAFrameworkCreate, BIAFrameworkUpdate]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(BIAFramework, db_session)

    async def create(self, *, obj_in: BIAFrameworkCreate, created_by_id: uuid.UUID, organization_id: uuid.UUID) -> BIAFramework:
        """
        Create a new BIA Framework, including its parameters and RTOs.
        The Pydantic validator on the schema ensures weightages sum to 100.
        """
        framework_data = obj_in.model_dump(exclude={'parameters', 'rtos'})
        
        db_obj = BIAFramework(
            **framework_data,
            created_by_id=created_by_id,
            updated_by_id=created_by_id, # On creation, updater is the creator
            organization_id=organization_id
        )

        # Create and associate parameter and RTO objects
        db_obj.parameters = [BIAFrameworkParameter(**p.model_dump()) for p in obj_in.parameters]
        db_obj.rtos = [BIAFrameworkRTO(**r.model_dump()) for r in obj_in.rtos]

        self.db_session.add(db_obj)
        await self.db_session.commit()
        await self.db_session.refresh(db_obj, ['parameters', 'rtos'])
        return db_obj

    async def update(self, *, db_obj: BIAFramework, obj_in: BIAFrameworkUpdate, updated_by_id: uuid.UUID) -> BIAFramework:
        """
        Update a BIA Framework.
        This handles updates to the framework's own fields and replaces its parameters and RTOs if they are provided in the update payload.
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Update the base framework fields
        for field, value in update_data.items():
            if field not in ['parameters', 'rtos']:
                setattr(db_obj, field, value)
        
        db_obj.updated_by_id = updated_by_id

        # If parameters are provided, replace the existing ones
        if 'parameters' in update_data and update_data['parameters'] is not None:
            # This relies on the cascade="all, delete-orphan" setting in the model relationship
            db_obj.parameters = [BIAFrameworkParameter(**p.model_dump()) for p in obj_in.parameters]

        # If RTOs are provided, replace the existing ones
        if 'rtos' in update_data and update_data['rtos'] is not None:
            db_obj.rtos = [BIAFrameworkRTO(**r.model_dump()) for r in obj_in.rtos]

        self.db_session.add(db_obj)
        await self.db_session.commit()
        await self.db_session.refresh(db_obj, ['parameters', 'rtos'])
        return db_obj

    async def get(self, id: uuid.UUID) -> Optional[BIAFramework]:
        """
        Get a BIA Framework by its ID, eagerly loading its parameters and RTOs.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == id)
            .options(
                selectinload(self.model.parameters).selectinload(BIAFrameworkParameter.criterion),
                selectinload(self.model.rtos)
            )
        )
        result = await self.db_session.execute(stmt)
        return result.scalars().first()
