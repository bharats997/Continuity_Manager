import uuid
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

# Shared properties
class PermissionBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Permission name, e.g., user_create, department_read")
    description: Optional[str] = Field(None, max_length=255, description="Detailed description of what the permission allows")
    # category: Optional[str] = Field(None, max_length=50, description="Optional category to group permissions, e.g., User Management, Financials")

# Properties to receive via API on creation (permissions are typically system-defined, so Create might not be exposed via API)
class PermissionCreate(PermissionBase):
    pass

# Properties to receive via API on update (permissions are typically system-defined, so Update might not be exposed via API)
class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    # category: Optional[str] = Field(None, max_length=50)

# Properties shared by models stored in DB
class PermissionInDBBase(PermissionBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

# Additional properties to return via API
class PermissionRead(PermissionInDBBase):
    pass

# Additional properties stored in DB
class PermissionInDB(PermissionInDBBase):
    pass
