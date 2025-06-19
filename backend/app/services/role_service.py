# backend/app/services/role_service.py
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from fastapi import HTTPException, status

from ..models.domain.roles import Role as RoleDB
from ..models.domain.permissions import Permission as PermissionModel
from ..schemas.role import RoleCreate, RoleUpdate

class RoleService:
    async def get_role_by_id(self, db: AsyncSession, role_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[RoleDB]:
        query = select(RoleDB).options(joinedload(RoleDB.permissions)).filter(RoleDB.id == role_id, RoleDB.organization_id == organization_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_role_by_name(self, db: AsyncSession, name: str, organization_id: uuid.UUID) -> Optional[RoleDB]:
        query = select(RoleDB).options(joinedload(RoleDB.permissions)).filter(RoleDB.name == name, RoleDB.organization_id == organization_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_roles(self, db: AsyncSession, organization_id: uuid.UUID, skip: int = 0, limit: int = 100, name_filter: Optional[str] = None, sort_by: Optional[str] = None, sort_order: Optional[str] = "asc") -> List[RoleDB]:
        query = select(RoleDB).options(joinedload(RoleDB.permissions)).filter(RoleDB.organization_id == organization_id)

        if name_filter:
            query = query.filter(RoleDB.name.ilike(f"%{name_filter}%"))

        if sort_by:
            sort_column = getattr(RoleDB, sort_by, None)
            if sort_column:
                if sort_order.lower() == "desc":
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(RoleDB.name.asc())

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def create_role(self, db: AsyncSession, role_in: RoleCreate, organization_id: uuid.UUID) -> RoleDB:
        existing_role = await self.get_role_by_name(db, name=role_in.name, organization_id=organization_id)
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role with name '{role_in.name}' already exists."
            )
        
        db_role = RoleDB(name=role_in.name, description=role_in.description, organization_id=organization_id)
        
        if role_in.permission_ids:
            perm_query = select(PermissionModel).filter(PermissionModel.id.in_(role_in.permission_ids))
            permissions_result = await db.execute(perm_query)
            permissions = permissions_result.scalars().all()
            if len(permissions) != len(set(role_in.permission_ids)):
                found_ids = {p.id for p in permissions}
                missing_ids_set = set(role_in.permission_ids) - found_ids
                missing_ids_str = ', '.join(str(uid) for uid in missing_ids_set)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"One or more permission IDs not found: {missing_ids_str}."
                )
            db_role.permissions = permissions
            
        db.add(db_role)
        await db.commit()
        await db.refresh(db_role)
        await db.refresh(db_role, attribute_names=['permissions'])
        return db_role

    async def update_role(self, db: AsyncSession, role_id: uuid.UUID, role_in: RoleUpdate, organization_id: uuid.UUID) -> Optional[RoleDB]:
        db_role = await self.get_role_by_id(db, role_id=role_id, organization_id=organization_id)
        if not db_role:
            return None

        update_data = role_in.model_dump(exclude_unset=True)

        if 'name' in update_data and update_data['name'] != db_role.name:
            existing_role_with_new_name = await self.get_role_by_name(db, name=update_data['name'], organization_id=organization_id)
            if existing_role_with_new_name and existing_role_with_new_name.id != role_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Role with name '{update_data['name']}' already exists."
                )
            db_role.name = update_data['name']

        if 'description' in update_data:
            db_role.description = update_data['description']

        if role_in.permission_ids is not None:
            if not role_in.permission_ids:
                db_role.permissions = []
            else:
                perm_query = select(PermissionModel).filter(PermissionModel.id.in_(role_in.permission_ids))
                permissions_result = await db.execute(perm_query)
                permissions = permissions_result.scalars().all()
                if len(permissions) != len(set(role_in.permission_ids)):
                    found_ids = {p.id for p in permissions}
                    missing_ids_set = set(role_in.permission_ids) - found_ids
                    missing_ids_str = ', '.join(str(uid) for uid in missing_ids_set)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"One or more permission IDs not found for update: {missing_ids_str}."
                    )
                db_role.permissions = permissions
        
        db.add(db_role)
        await db.commit()
        await db.refresh(db_role)
        await db.refresh(db_role, attribute_names=['permissions'])
        return db_role

    async def delete_role(self, db: AsyncSession, role_id: uuid.UUID, organization_id: uuid.UUID) -> bool:
        role_db = await self.get_role_by_id(db, role_id=role_id, organization_id=organization_id)
        if not role_db:
            return False
        
        await db.delete(role_db)
        await db.commit()
        return True

role_service = RoleService()
