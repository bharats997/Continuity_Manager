# backend/app/models/role.py
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field # Import Field
from .permission import PermissionSchema  # Import the Pydantic PermissionSchema

# Shared properties
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

# Properties to receive on role creation
class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = Field(default_factory=list, description="List of permission IDs to associate with the role")

# Properties to receive on role update
class RoleUpdate(RoleBase):
    name: Optional[str] = None # Name might be updatable for description, but typically fixed if used in code
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = Field(None, description="List of permission IDs to associate. If provided, replaces existing permissions.")

# Properties shared by models stored in DB
class RoleInDBBase(RoleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Properties to return to client
class RoleSchema(RoleInDBBase): # Renamed from Role to RoleSchema
    permissions: List[PermissionSchema] = Field(default_factory=list, description="List of permissions associated with the role")

# Properties stored in DB
class RoleInDB(RoleInDBBase):
    pass


# --- SQLAlchemy Model ---
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

# Import Base, user_roles_table, and role_permissions_table from the package's __init__.py
from . import Base, user_roles_table, role_permissions_table

class Role(Base): # This is the SQLAlchemy model
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    # Relationship to Person via user_roles_table
    # The "Person" string will be resolved by SQLAlchemy to the Person class.
    persons = relationship("Person", secondary=user_roles_table, back_populates="roles")

    # Relationship to Permission via role_permissions_table
    # The "Permission" string will be resolved by SQLAlchemy to the Permission class.
    permissions = relationship("Permission", secondary=role_permissions_table, back_populates="roles")

