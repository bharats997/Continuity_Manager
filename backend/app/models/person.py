# backend/app/models/person.py
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

# Forward references for Department and Location if they are in other model files
# from .department import Department  # Assuming Department model exists
# from .location import Location  # Assuming Location model exists
from .role import Role # Import Role model

# Shared properties
class PersonBase(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    jobTitle: Optional[str] = None
    departmentId: Optional[int] = None
    locationId: Optional[int] = None # As per PRD for FR 1.2

# Properties to receive on person creation
class PersonCreate(PersonBase):
    roleIds: List[int] # List of role IDs to assign

# Properties to receive on person update
class PersonUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
    jobTitle: Optional[str] = None
    departmentId: Optional[int] = None
    locationId: Optional[int] = None
    isActive: Optional[bool] = None
    roleIds: Optional[List[int]] = None # To update assigned roles

# Properties shared by models stored in DB
class PersonInDBBase(PersonBase):
    id: int
    organizationId: int
    isActive: bool
    createdAt: datetime
    updatedAt: datetime
    createdBy: Optional[int] = None
    updatedBy: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

# Properties to return to client
class Person(PersonInDBBase):
    roles: List[Role] = []
    # department: Optional[Department] = None # To be added once Department model is confirmed
    # location: Optional[Location] = None   # To be added once Location model is confirmed

# Properties stored in DB
class PersonInDB(PersonInDBBase):
    pass

