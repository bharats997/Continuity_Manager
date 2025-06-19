# backend/app/services/base_service.py
from typing import TypeVar, Generic, Type, Any, Optional, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from app.db.session import Base # Assuming Base is your SQLAlchemy declarative base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        """
        Base class for services, providing common CRUD operations.

        :param model: The SQLAlchemy model class
        :param db_session: The SQLAlchemy async session
        """
        self.model = model
        self.db_session = db_session

    async def get(self, id: Any) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, *, obj_in: CreateSchemaType, **kwargs: Any) -> ModelType:
        obj_in_data = dict(obj_in)
        # Add any additional kwargs passed, e.g., created_by_id
        db_obj = self.model(**obj_in_data, **kwargs)
        self.db_session.add(db_obj)
        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        return db_obj

    async def update(
        self, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, dict[str, Any]], **kwargs: Any
    ) -> ModelType:
        obj_data = db_obj.__dict__
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        # Add any additional kwargs passed, e.g., updated_by_id
        for key, value in kwargs.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        self.db_session.add(db_obj)
        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        return db_obj

    async def remove(self, *, id: Any) -> Optional[ModelType]:
        obj = await self.get(id)
        if obj:
            await self.db_session.delete(obj)
            await self.db_session.commit()
        return obj
