# backend/app/models/role.py
import uuid
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from .permission import PermissionSchema

class RoleName(str, Enum):
    SUPER_ADMIN = "Super Admin"
    ADMIN = "Admin"
    BCM_MANAGER = "BCM Manager"
    CISO = "CISO"
    INTERNAL_AUDITOR = "Internal Auditor"
    DEPARTMENT_MANAGER = "Department Manager"
    USER = "User"
    # Add other roles as needed based on PRD

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


# Shared properties
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

# Properties to receive on role creation
class RoleCreate(RoleBase):
    permission_ids: Optional[List[uuid.UUID]] = Field(default_factory=list, description="List of permission IDs to associate with the role")

# Properties to receive on role update
class RoleUpdate(RoleBase):
    name: Optional[str] = None # Name might be updatable for description, but typically fixed if used in code
    description: Optional[str] = None
    permission_ids: Optional[List[uuid.UUID]] = Field(None, description="List of permission IDs to associate. If provided, replaces existing permissions.")

# Properties shared by models stored in DB
class RoleInDBBase(RoleBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# Properties to return to client
class RoleSchema(RoleInDBBase): # Renamed from Role to RoleSchema
    permissions: List[PermissionSchema] = Field(default_factory=list, description="List of permissions associated with the role")

# Properties stored in DB
class RoleInDB(RoleInDBBase):
    pass
