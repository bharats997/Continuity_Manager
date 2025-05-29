# backend/app/models/location.py
from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

# Shared properties
class LocationBase(BaseModel):
    name: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: str
    isActive: Optional[bool] = True

# Properties to receive on location creation
class LocationCreate(LocationBase):
    organizationId: int # Must be provided during creation

# Properties to receive on location update
class LocationUpdate(BaseModel):
    name: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    isActive: Optional[bool] = None

# Properties shared by models stored in DB
class LocationInDBBase(LocationBase):
    id: int
    organizationId: int # Ensure this is part of the DB model representation
    createdAt: datetime
    updatedAt: datetime
    # createdBy: Optional[int] = None # If tracking users
    # updatedBy: Optional[int] = None # If tracking users

    model_config = ConfigDict(from_attributes=True)

# Properties to return to client (main Location model)
class Location(LocationInDBBase):
    pass

# For listing multiple locations
class LocationListResponse(BaseModel):
    items: list[Location]
    total: int
