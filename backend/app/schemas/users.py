import uuid
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, ConfigDict

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: bool = True
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization_id: Optional[uuid.UUID] = None

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str = Field(..., min_length=8)
    organization_id: uuid.UUID
    # role_ids: Optional[List[uuid.UUID]] = None # Example if roles are assigned at creation

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=8)
    # email: Optional[EmailStr] = None # Email updates might be restricted
    # is_active: Optional[bool] = None
    # first_name: Optional[str] = None
    # last_name: Optional[str] = None
    # organization_id: Optional[uuid.UUID] = None # Org changes might be restricted

# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

# Additional properties to return via API
class UserRead(UserInDBBase):
    # Add other fields to return, e.g., roles
    # from .roles import RoleRead # Assuming RoleRead schema exists
    # roles: List[RoleRead] = []
    pass

# Additional properties stored in DB (including hashed password)
class UserInDB(UserInDBBase):
    password_hash: str

# Schema for user login
class UserLogin(BaseModel):
    email: EmailStr
    password: str
