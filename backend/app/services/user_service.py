# backend/app/services/user_service.py
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from ..models.domain.users import User as UserDB
from ..models.domain.roles import Role as RoleDB
from ..schemas.user_schemas import UserCreate, UserUpdate
from ..services.department_service import department_service
from ..services.location_service import location_service
from core.security import get_password_hash

class UserService:
    async def get_user_by_id(
        self, db: AsyncSession, *, user_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Optional[UserDB]:
        from sqlalchemy.orm import selectinload # Add import here for clarity
        from ..models.domain.roles import Role as RoleDB # Ensure RoleDB is available for relationship path

        stmt = (
            select(UserDB)
            .options(
                selectinload(UserDB.organization),
                selectinload(UserDB.roles).selectinload(RoleDB.permissions),
                selectinload(UserDB.department), # Eager load department
                selectinload(UserDB.location)    # Eager load location
            )
            .filter(
                UserDB.id == user_id,
                UserDB.organization_id == organization_id # Corrected typo: organizationId -> organization_id
            )
        )
        result = await db.execute(stmt)
        return result.unique().scalar_one_or_none() # Use .unique() due to eager loads

    async def get_user_by_email(
        self, db: AsyncSession, *, email: str, organization_id: uuid.UUID
    ) -> Optional[UserDB]:
        result = await db.execute(
            select(UserDB).filter(
                UserDB.email == email,
                UserDB.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()

    async def get_users(
        self, db: AsyncSession, *, organization_id: uuid.UUID, skip: int = 0, limit: int = 100,
        is_active: Optional[bool] = True
    ) -> List[UserDB]:
        query = select(UserDB).options(
            selectinload(UserDB.organization),
            selectinload(UserDB.roles).selectinload(RoleDB.permissions),
            selectinload(UserDB.department),
            selectinload(UserDB.location)
        ).filter(UserDB.organization_id == organization_id)
        if is_active is not None:
            query = query.filter(UserDB.is_active == is_active)
        result = await db.execute(
            query.order_by(UserDB.last_name, UserDB.first_name).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create_user(
        self, db: AsyncSession, *, user_in: UserCreate, organization_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> UserDB:
        existing_user = await self.get_user_by_email(db, email=user_in.email, organization_id=organization_id)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists in this organization.",
            )

        if user_in.departmentId:
            department = await department_service.get_department_by_id(
                db, department_id=user_in.departmentId, organization_id=organization_id
            )
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Department with ID {user_in.departmentId} not found in this organization.",
                )
        
        if user_in.locationId:
            location = await location_service.get_location_by_id(
                db, location_id=user_in.locationId, organization_id=organization_id
            )
            if not location:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Location with ID {user_in.location_id} not found in organization {organization_id}."
                )

        hashed_password = get_password_hash(user_in.password)
        db_user = UserDB(
            **user_in.model_dump(exclude={"roleIds", "password"}),
            password_hash=hashed_password,
            created_by=current_user_id,
            updated_by=current_user_id,
            organization_id=organization_id
        )

        if user_in.roleIds:
            roles_result = await db.execute(select(RoleDB).filter(RoleDB.id.in_(user_in.roleIds), RoleDB.organization_id == organization_id))
            roles = roles_result.scalars().all()
            if len(roles) != len(set(user_in.roleIds)):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="One or more role IDs are invalid or do not belong to this organization.",
                )
            db_user.roles = roles
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def update_user(
        self, db: AsyncSession, *, user_db: UserDB, user_in: UserUpdate, current_user_id: uuid.UUID
    ) -> UserDB:
        update_data = user_in.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            user_db.password_hash = hashed_password
            del update_data["password"]

        if "email" in update_data and update_data["email"] != user_db.email:
            existing_user = await self.get_user_by_email(db, email=update_data["email"], organization_id=user_db.organization_id)
            if existing_user and existing_user.id != user_db.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with this email already exists in this organization.",
                )
        
        if "departmentId" in update_data and update_data["departmentId"] is not None:
            department = await department_service.get_department_by_id(
                db, department_id=update_data["departmentId"], organization_id=user_db.organization_id
            )
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Department with ID {update_data['departmentId']} not found in this organization.",
                )
        
        if "locationId" in update_data and update_data["locationId"] is not None:
            location = await location_service.get_location_by_id(
                db, location_id=update_data["locationId"], organization_id=user_db.organization_id
            )
            if not location:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Location with ID {update_data['locationId']} not found in organization {user_db.organizationId}."
                )

        for field, value in update_data.items():
            if field != "roleIds":
                setattr(user_db, field, value)
        
        if "roleIds" in update_data and update_data["roleIds"] is not None:
            roles_result = await db.execute(select(RoleDB).filter(RoleDB.id.in_(update_data["roleIds"]), RoleDB.organization_id == user_db.organization_id))
            roles = roles_result.scalars().all()
            if len(roles) != len(set(update_data["roleIds"])):
                 raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="One or more role IDs are invalid or do not belong to this organization for update.",
                )
            user_db.roles = roles
        
        user_db.updatedBy = current_user_id
        db.add(user_db)
        await db.commit()
        await db.refresh(user_db)
        return user_db

    async def soft_delete_user(self, db: AsyncSession, *, user_db: UserDB, current_user_id: uuid.UUID) -> UserDB:
        if not user_db.isActive:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already inactive.",
            )
        user_db.isActive = False
        user_db.updatedBy = current_user_id
        db.add(user_db)
        await db.commit()
        await db.refresh(user_db)
        return user_db

user_service = UserService()
