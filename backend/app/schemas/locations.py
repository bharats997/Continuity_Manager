import uuid
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

# Shared properties
class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address_line_1: Optional[str] = Field(None, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state_province_region: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    organization_id: uuid.UUID

# Properties to receive via API on creation
class LocationCreate(LocationBase):
    pass

# Properties to receive via API on update
class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address_line_1: Optional[str] = Field(None, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state_province_region: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # organization_id cannot be updated

# Properties shared by models stored in DB
class LocationInDBBase(LocationBase):
    id: uuid.UUID
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)

# Additional properties to return via API
class LocationRead(LocationInDBBase):
    pass

# Additional properties stored in DB
class LocationInDB(LocationInDBBase):
    pass
