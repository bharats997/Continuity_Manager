import uuid
from typing import Any, Dict, Optional, Union, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.domain.roles import Role # Assuming Role model is in app.models.roles
from app.models.domain.permissions import Permission # Assuming Permission model is in app.models.permissions
from app.schemas.roles import RoleCreate, RoleUpdate

class CRUDRole:
    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Role]:
        result = await db.execute(
            select(Role).options(selectinload(Role.permissions)).filter(Role.id == id)
        )
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, *, name: str, organization_id: uuid.UUID) -> Optional[Role]:
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .filter(Role.name == name, Role.organization_id == organization_id)
        )
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Role]:
        result = await db.execute(
            select(Role).options(selectinload(Role.permissions)).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_multi_by_organization(
        self, db: AsyncSession, *, organization_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Role]:
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .filter(Role.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: RoleCreate) -> Role:
        db_obj = Role(
            name=obj_in.name,
            description=obj_in.description,
            organization_id=obj_in.organization_id,
            is_system_role=obj_in.is_system_role
        )
        if obj_in.permission_ids:
            permissions = await db.execute(
                select(Permission).filter(Permission.id.in_(obj_in.permission_ids))
            )
            db_obj.permissions = permissions.scalars().all()
            
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: Role, obj_in: Union[RoleUpdate, Dict[str, Any]]
    ) -> Role:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "permission_ids":
                if value is not None: # Allow clearing permissions with empty list
                    permissions = await db.execute(
                        select(Permission).filter(Permission.id.in_(value))
                    )
                    db_obj.permissions = permissions.scalars().all()
                else: # If permission_ids is None, don't change existing permissions
                    pass
            elif hasattr(db_obj, field):
                setattr(db_obj, field, value)
            
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        # Eager load permissions again after refresh if they are accessed
        await db.refresh(db_obj, attribute_names=['permissions'])
        return db_obj

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Role]:
        obj = await self.get(db, id=id)
        if obj:
            if obj.is_system_role:
                # Potentially raise an error or handle differently
                # For now, we'll prevent deletion of system roles
                return None # Or raise HTTPException(status_code=403, detail="Cannot delete system roles")
            await db.delete(obj)
            await db.commit()
        return obj

    async def add_permissions_to_role(self, db: AsyncSession, *, role_id: uuid.UUID, permission_ids: List[uuid.UUID]) -> Optional[Role]:
        role = await self.get(db, id=role_id)
        if not role:
            return None
        
        permissions_to_add_result = await db.execute(
            select(Permission).filter(Permission.id.in_(permission_ids))
        )
        permissions_to_add = permissions_to_add_result.scalars().all()
        
        for perm in permissions_to_add:
            if perm not in role.permissions:
                role.permissions.append(perm)
        
        await db.commit()
        await db.refresh(role)
        await db.refresh(role, attribute_names=['permissions'])
        return role

    async def remove_permissions_from_role(self, db: AsyncSession, *, role_id: uuid.UUID, permission_ids: List[uuid.UUID]) -> Optional[Role]:
        role = await self.get(db, id=role_id)
        if not role:
            return None

        # Create a list of permissions to remove by ID
        current_permission_ids = {p.id for p in role.permissions}
        permissions_to_remove_ids = [pid for pid in permission_ids if pid in current_permission_ids]

        if permissions_to_remove_ids:
            # Filter current permissions to keep only those not in the removal list
            role.permissions = [p for p in role.permissions if p.id not in permissions_to_remove_ids]
        
        await db.commit()
        await db.refresh(role)
        await db.refresh(role, attribute_names=['permissions'])
        return role

role = CRUDRole()
