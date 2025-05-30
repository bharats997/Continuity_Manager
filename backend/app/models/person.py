# backend/app/models/person.py
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict # Ensure ConfigDict is imported
from datetime import datetime

# Forward references for Department and Location if they are in other model files
# from .department import Department
# from .location import Location
from .role import RoleSchema  # Import Pydantic RoleSchema

# --- Pydantic Models ---
class PersonBase(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    jobTitle: Optional[str] = None
    departmentId: Optional[int] = None
    locationId: Optional[int] = None

class PersonCreate(PersonBase):
    roleIds: List[int] # List of role IDs to assign
    # You might also want to include password here for creation
    # password: str 

class PersonUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
    jobTitle: Optional[str] = None
    departmentId: Optional[int] = None
    locationId: Optional[int] = None
    isActive: Optional[bool] = None
    roleIds: Optional[List[int]] = None

class PersonInDBBase(PersonBase):
    id: int
    organizationId: int # Assuming this comes from somewhere
    isActive: bool
    createdAt: datetime
    updatedAt: datetime
    # createdBy: Optional[int] = None # Add if part of your schema
    # updatedBy: Optional[int] = None # Add if part of your schema
    model_config = ConfigDict(from_attributes=True)

# Pydantic model for API responses (renamed from Person to PersonSchema)
class PersonSchema(PersonInDBBase): 
    roles: List[RoleSchema] = [] # Use Pydantic RoleSchema

class PersonInDB(PersonInDBBase): # For data retrieved from DB including sensitive fields
    hashed_password: str


# --- SQLAlchemy Model ---
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey as SQLForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime as dt_sqlalchemy # Alias for SQLAlchemy's datetime usage

# Import Base and user_roles_table from the package's __init__.py
from . import Base, user_roles_table

class Person(Base): # This is the SQLAlchemy model
    __tablename__ = 'persons'

    id = Column(Integer, primary_key=True, index=True)
    firstName = Column(String(100), nullable=False)
    lastName = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    jobTitle = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)

    # Assuming these foreign keys point to tables defined by other SQLAlchemy models
    departmentId = Column(Integer, SQLForeignKey('departments.id'), nullable=True) 
    locationId = Column(Integer, SQLForeignKey('locations.id'), nullable=True)   
    organizationId = Column(Integer, SQLForeignKey('organizations.id'), nullable=False) 

    isActive = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=dt_sqlalchemy.utcnow)
    updatedAt = Column(DateTime, default=dt_sqlalchemy.utcnow, onupdate=dt_sqlalchemy.utcnow)

    # Relationship to Role (SQLAlchemy model) via user_roles_table
    roles = relationship("Role", secondary=user_roles_table, back_populates="persons")

    model_config = ConfigDict(from_attributes=True)

# Properties to return to client
class Person(PersonInDBBase):
    roles: List[RoleSchema] = [] # Corrected to use RoleSchema
    # department: Optional[Department] = None # To be added once Department model is confirmed
    # location: Optional[Location] = None   # To be added once Location model is confirmed

# Properties stored in DB
class PersonInDB(PersonInDBBase):
    pass

