# backend/app/models/user_schemas.py
import uuid
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import datetime

# Forward references for Department and Location if they are in other model files
# from .department import Department # Assuming Department schema might be needed
# from .location import Location # Assuming Location schema might be needed
from .role import RoleSchema  # Import Pydantic RoleSchema

# --- Pydantic Models ---
class UserBase(BaseModel):
    firstName: str = Field(..., alias='first_name')
    lastName: str = Field(..., alias='last_name')
    email: EmailStr
    jobTitle: Optional[str] = Field(None, alias='job_title')
    departmentId: Optional[uuid.UUID] = Field(None, alias='department_id')
    locationId: Optional[uuid.UUID] = Field(None, alias='location_id')

class UserCreate(UserBase):
    password: str  # Added password field for user creation
    roleIds: List[uuid.UUID] # List of role IDs to assign

class UserUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
    jobTitle: Optional[str] = None
    departmentId: Optional[uuid.UUID] = None
    locationId: Optional[uuid.UUID] = None
    isActive: Optional[bool] = None
    roleIds: Optional[List[uuid.UUID]] = None

class UserInDBBase(UserBase):
    id: uuid.UUID
    organizationId: uuid.UUID = Field(..., alias='organization_id')
    isActive: bool = Field(..., alias='is_active')
    createdAt: datetime = Field(..., alias='created_at')
    updatedAt: datetime = Field(..., alias='updated_at')
    createdBy: Optional[uuid.UUID] = Field(None, alias='created_by_id') # Assuming model has created_by_id
    updatedBy: Optional[uuid.UUID] = Field(None, alias='updated_by_id') # Assuming model has updated_by_id
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# Pydantic model for API responses
class UserSchema(UserInDBBase): 
    roles: List[RoleSchema] = [] # Use Pydantic RoleSchema

class UserInDB(UserInDBBase): # For data retrieved from DB including sensitive fields
    hashed_password: str

class UserSimpleResponse(BaseModel):
    id: uuid.UUID
    firstName: str = Field(..., alias='first_name')
    lastName: str = Field(..., alias='last_name')
    email: EmailStr

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
