# backend/app/models/role.py
from typing import Optional
from pydantic import BaseModel, ConfigDict

# Shared properties
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

# Properties to receive on role creation
class RoleCreate(RoleBase):
    pass

# Properties to receive on role update
class RoleUpdate(RoleBase):
    name: Optional[str] = None # Name might be updatable for description, but typically fixed if used in code
    description: Optional[str] = None

# Properties shared by models stored in DB
class RoleInDBBase(RoleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Properties to return to client
class Role(RoleInDBBase):
    pass

# Properties stored in DB
class RoleInDB(RoleInDBBase):
    pass
