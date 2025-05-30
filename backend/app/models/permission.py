# backend/app/models/permission.py
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

# Shared properties
class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

# Properties to receive on permission creation
class PermissionCreate(PermissionBase):
    pass

# Properties to receive on permission update
class PermissionUpdate(PermissionBase):
    name: Optional[str] = None # Usually fixed if used as an identifier
    description: Optional[str] = None

# Properties shared by models stored in DB
class PermissionInDBBase(PermissionBase):
    id: int
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)

# Properties to return to client
class PermissionSchema(PermissionInDBBase): # Renamed from Permission to PermissionSchema
    pass

# Properties stored in DB
class PermissionInDB(PermissionInDBBase):
    pass


# --- SQLAlchemy Model ---
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime as dt_sqlalchemy # Alias for SQLAlchemy's datetime usage

# Import Base and role_permissions_table from the package's __init__.py
from . import Base, role_permissions_table

class Permission(Base): # This is the SQLAlchemy model
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False) # e.g., "user:create", "post:edit"
    description = Column(Text, nullable=True)
    
    createdAt = Column(DateTime, default=dt_sqlalchemy.utcnow)
    updatedAt = Column(DateTime, default=dt_sqlalchemy.utcnow, onupdate=dt_sqlalchemy.utcnow)

    # Relationship to Role via role_permissions_table
    # The "Role" string will be resolved by SQLAlchemy to the Role class.
    roles = relationship("Role", secondary=role_permissions_table, back_populates="permissions")

