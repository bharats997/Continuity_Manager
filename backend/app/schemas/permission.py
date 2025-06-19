# backend/app/models/permission.py
import uuid  # Added import
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
    id: uuid.UUID
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# Properties to return to client
class PermissionSchema(PermissionInDBBase): # Renamed from Permission to PermissionSchema
    pass

# Properties stored in DB
class PermissionInDB(PermissionInDBBase):
    pass
