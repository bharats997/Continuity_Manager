# backend/app/models/application.py
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# Assuming .person.Person is a Pydantic model suitable for response (e.g., has from_attributes=True)
# This is consistent with MEMORY b2812ac1-7132-4988-8f25-a8ef0cd20a30
from .person import Person as PersonResponse

# Assuming .organization.Organization is a Pydantic model suitable for response.
# If it's not (e.g., lacks from_attributes=True), backend/app/models/organization.py may need an update.
from .organization import OrganizationResponse as OrganizationResponsePydantic


class ApplicationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    organizationId: int
    appOwnerId: Optional[int] = None
    applicationType: Optional[str] = Field(None, max_length=100) # E.g., SaaS, Custom Developed, COTS
    hostingEnvironment: Optional[str] = Field(None, max_length=100) # E.g., Cloud (AWS), On-Premise, Vendor Hosted
    criticality: Optional[str] = Field(None, max_length=50) # E.g., High, Medium, Low
    isActive: bool = True

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    # organizationId: Optional[int] = None # Typically, an application's organization is not changed via a simple update.
    appOwnerId: Optional[int] = None
    applicationType: Optional[str] = Field(None, max_length=100)
    hostingEnvironment: Optional[str] = Field(None, max_length=100)
    criticality: Optional[str] = Field(None, max_length=50)
    isActive: Optional[bool] = None

class ApplicationResponse(ApplicationBase):
    id: int
    createdAt: datetime
    updatedAt: datetime
    deletedAt: Optional[datetime] = None
    
    # Nested objects for relationships, populated by the service layer.
    # These correspond to relationships in the SQLAlchemy model.
    organization: Optional[OrganizationResponsePydantic] = None
    appOwner: Optional[PersonResponse] = None
    creator: Optional[PersonResponse] = None
    updater: Optional[PersonResponse] = None
    deleter: Optional[PersonResponse] = None

    model_config = ConfigDict(from_attributes=True)
