# backend/app/services/role_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.domain.roles import Role as RoleDB
from ..models.role import Role as RoleSchema

class RoleService:
    def get_role_by_id(self, db: Session, role_id: int) -> Optional[RoleDB]:
        return db.query(RoleDB).filter(RoleDB.id == role_id).first()

    def get_role_by_name(self, db: Session, name: str) -> Optional[RoleDB]:
        return db.query(RoleDB).filter(RoleDB.name == name).first()

    def get_roles(self, db: Session, skip: int = 0, limit: int = 100) -> List[RoleDB]:
        return db.query(RoleDB).offset(skip).limit(limit).all()

    # Roles are predefined, so create/update/delete are typically not exposed via API
    # but might be used internally or by super-admins if needed.
    # For now, we'll focus on read operations.

role_service = RoleService()
