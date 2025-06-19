import uuid
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

# Shared properties
class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    organization_id: uuid.UUID
    # head_of_department_id: Optional[uuid.UUID] = None # Link to a User

# Properties to receive via API on creation
class DepartmentCreate(DepartmentBase):
    pass

# Properties to receive via API on update
class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    # head_of_department_id: Optional[uuid.UUID] = None
    # organization_id cannot be updated for a department

# Properties shared by models stored in DB
class DepartmentInDBBase(DepartmentBase):
    id: uuid.UUID
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)

# Additional properties to return via API
class DepartmentRead(DepartmentInDBBase):
    # from ..users import UserRead # Example if linking HoD
    # head_of_department: Optional[UserRead] = None
    pass

# Additional properties stored in DB
class DepartmentInDB(DepartmentInDBBase):
    pass
