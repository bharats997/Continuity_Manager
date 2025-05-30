# backend/app/services/role_service.py
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from ..models.domain.roles import Role as RoleDB
from ..models.domain.permissions import Permission as PermissionModel
from ..models.role import RoleCreate, RoleUpdate # RoleSchema is not directly used here, but Role (Pydantic) is implicitly handled by FastAPI

class RoleService:
    def get_role_by_id(self, db: Session, role_id: int) -> Optional[RoleDB]:
        return db.query(RoleDB).options(joinedload(RoleDB.permissions)).filter(RoleDB.id == role_id).first()

    def get_role_by_name(self, db: Session, name: str) -> Optional[RoleDB]:
        return db.query(RoleDB).options(joinedload(RoleDB.permissions)).filter(RoleDB.name == name).first()

    def get_roles(self, db: Session, skip: int = 0, limit: int = 100) -> List[RoleDB]:
        return db.query(RoleDB).options(joinedload(RoleDB.permissions)).offset(skip).limit(limit).all()

    def create_role(self, db: Session, role_in: RoleCreate) -> RoleDB:
        existing_role = self.get_role_by_name(db, name=role_in.name)
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role with name '{role_in.name}' already exists."
            )
        
        db_role = RoleDB(name=role_in.name, description=role_in.description)
        
        if role_in.permission_ids:
            permissions = db.query(PermissionModel).filter(PermissionModel.id.in_(role_in.permission_ids)).all()
            if len(permissions) != len(set(role_in.permission_ids)):
                # Find which IDs were not found for a more specific error, or keep it general
                found_ids = {p.id for p in permissions}
                missing_ids = set(role_in.permission_ids) - found_ids
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"One or more permission IDs not found: {missing_ids}."
                )
            db_role.permissions = permissions
            
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        # Eager load permissions for the returned object if refresh doesn't handle it automatically for relationships
        # This is good practice to ensure the returned object matches what get_role_by_id would return.
        db.refresh(db_role, attribute_names=['permissions']) 
        return db_role

    def update_role(self, db: Session, role_id: int, role_in: RoleUpdate) -> Optional[RoleDB]:
        db_role = self.get_role_by_id(db, role_id=role_id) # This already loads permissions
        if not db_role:
            return None # Or raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

        update_data = role_in.model_dump(exclude_unset=True)

        if 'name' in update_data and update_data['name'] != db_role.name:
            existing_role_with_new_name = self.get_role_by_name(db, name=update_data['name'])
            if existing_role_with_new_name and existing_role_with_new_name.id != role_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Role with name '{update_data['name']}' already exists."
                )
            db_role.name = update_data['name']

        if 'description' in update_data:
            db_role.description = update_data['description']

        if role_in.permission_ids is not None: # Check if permission_ids was explicitly passed
            if not role_in.permission_ids: # Empty list means clear permissions
                db_role.permissions = []
            else:
                permissions = db.query(PermissionModel).filter(PermissionModel.id.in_(role_in.permission_ids)).all()
                if len(permissions) != len(set(role_in.permission_ids)):
                    found_ids = {p.id for p in permissions}
                    missing_ids = set(role_in.permission_ids) - found_ids
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"One or more permission IDs not found for update: {missing_ids}."
                    )
                db_role.permissions = permissions
        
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        db.refresh(db_role, attribute_names=['permissions'])
        return db_role

    # Consider adding delete_role if needed, e.g.:
    # def delete_role(self, db: Session, role_id: int) -> Optional[RoleDB]:
    #     db_role = self.get_role_by_id(db, role_id=role_id)
    #     if not db_role:
    #         return None # Or raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    #     db.delete(db_role)
    #     db.commit()
    #     return db_role # Return the deleted object (or its state before deletion)

role_service = RoleService()
