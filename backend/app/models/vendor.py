import uuid
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime

class VendorCriticality(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class VendorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    contact_person: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50) # Assuming E.164 format, can be adjusted
    service_provided: Optional[str] = Field(None, max_length=1000)
    criticality: Optional[VendorCriticality] = VendorCriticality.MEDIUM

    model_config = ConfigDict(use_enum_values=True, from_attributes=True) # For Pydantic V1, or json_encoders for V2 if needed

class VendorCreate(VendorBase):
    pass

class VendorUpdate(VendorBase):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    # All fields are optional for update

class VendorResponse(VendorBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[uuid.UUID] = None
    updated_by_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)
