import uuid
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, ConfigDict

# Shared properties
class VendorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    website: Optional[HttpUrl] = None
    contact_email: Optional[str] = Field(None, max_length=255) # Consider EmailStr if strict validation needed
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500) # Simple address field
    organization_id: uuid.UUID

# Properties to receive via API on creation
class VendorCreate(VendorBase):
    pass

# Properties to receive via API on update
class VendorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    website: Optional[HttpUrl] = None
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    # organization_id cannot be updated

# Properties shared by models stored in DB
class VendorInDBBase(VendorBase):
    id: uuid.UUID
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)

# Additional properties to return via API
class VendorRead(VendorInDBBase):
    pass

# Additional properties stored in DB
class VendorInDB(VendorInDBBase):
    pass
