import uuid
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict #, AnyUrl

# Shared properties
class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    # industry: Optional[str] = Field(None, max_length=100)
    # website: Optional[AnyUrl] = None # Requires pydantic.AnyUrl

# Properties to receive via API on creation
class OrganizationCreate(OrganizationBase):
    pass

# Properties to receive via API on update
class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    # industry: Optional[str] = Field(None, max_length=100)
    # website: Optional[AnyUrl] = None

# Properties shared by models stored in DB
class OrganizationInDBBase(OrganizationBase):
    id: uuid.UUID
    isActive: bool = Field(True, alias='is_active') # Organizations can be deactivated
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# Additional properties to return via API
class OrganizationRead(OrganizationInDBBase):
    pass

# Additional properties stored in DB
class OrganizationInDB(OrganizationInDBBase):
    pass
