import uuid
from typing import Optional

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# Shared properties
class BIACategoryBase(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)


# Properties to receive on item creation
class BIACategoryCreate(BIACategoryBase):
    name: str = Field(..., min_length=1, max_length=255)  # Name is required for creation


# Properties to receive on item update
class BIACategoryUpdate(BIACategoryBase):
    pass


# Properties shared by models stored in DB
class BIACategoryInDBBase(BIACategoryBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_id: uuid.UUID
    updated_by_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class BIACategoryRead(BIACategoryInDBBase):
    pass


# Properties stored in DB
class BIACategoryInDB(BIACategoryInDBBase):
    pass
