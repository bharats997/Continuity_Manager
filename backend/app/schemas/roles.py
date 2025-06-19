import uuid
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

# Shared properties
class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    organization_id: uuid.UUID
    is_system_role: bool = False # Indicates if the role is a system-defined, non-modifiable role

# Properties to receive via API on creation
class RoleCreate(RoleBase):
    permission_ids: Optional[List[uuid.UUID]] = []

# Properties to receive via API on update
class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    permission_ids: Optional[List[uuid.UUID]] = None
    # organization_id cannot be updated for a role
    # is_system_role cannot be updated

# Properties shared by models stored in DB
class RoleInDBBase(RoleBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

# Additional properties to return via API
class RoleRead(RoleInDBBase):
    # from .permissions import PermissionRead # Assuming PermissionRead schema exists
    # permissions: List[PermissionRead] = []
    pass

# Additional properties stored in DB
class RoleInDB(RoleInDBBase):
    pass # No additional fields like password_hash for roles
