import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from ..models.domain.applications import ApplicationStatusEnum, ApplicationType
from ..schemas.organizations import OrganizationRead as OrganizationResponse
from .user_schemas import UserSimpleResponse

# --- Base Schema ---

class ApplicationBase(BaseModel):
    """Shared properties for an application."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: ApplicationType
    hostedOn: Optional[str] = Field(None, alias='hosted_on', max_length=255, description="e.g., AWS, Azure, On-Premise DC1")
    status: ApplicationStatusEnum
    version: Optional[str] = Field(None, max_length=50)
    vendor: Optional[str] = Field(None, max_length=255)
    criticality: Optional[str] = Field(None, max_length=50, description="e.g., High, Medium, Low")
    workarounds: Optional[str] = None
    derivedRTO: Optional[str] = Field(None, alias="derived_rto", max_length=50)

    model_config = ConfigDict(populate_by_name=True)


# --- Schemas for API Operations (Create/Update) ---

class ApplicationCreate(ApplicationBase):
    """Properties to receive via API on creation."""
    organizationId: uuid.UUID = Field(..., alias='organization_id')
    appOwnerId: uuid.UUID = Field(..., alias='app_owner_id')


class ApplicationUpdate(BaseModel):
    """Properties to receive via API on update. All fields are optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    type: Optional[ApplicationType] = None
    hostedOn: Optional[str] = Field(None, alias='hosted_on', max_length=255)
    status: Optional[ApplicationStatusEnum] = None
    appOwnerId: Optional[uuid.UUID] = Field(None, alias='app_owner_id')
    version: Optional[str] = Field(None, max_length=50)
    vendor: Optional[str] = Field(None, max_length=255)
    criticality: Optional[str] = Field(None, max_length=50)
    workarounds: Optional[str] = None
    derivedRTO: Optional[str] = Field(None, alias="derived_rto", max_length=50)

    model_config = ConfigDict(populate_by_name=True)


# --- Schema for API Responses (Read) ---

class ApplicationRead(ApplicationBase):
    """Properties to return via API, including resolved relationships."""
    id: uuid.UUID
    
    # Audit fields
    createdAt: datetime = Field(..., alias='created_at')
    updatedAt: datetime = Field(..., alias='updated_at')
    
    # Resolved relationship objects
    organization: Optional[OrganizationResponse] = None
    appOwner: Optional[UserSimpleResponse] = Field(None, alias='app_owner')
    createdBy: Optional[UserSimpleResponse] = Field(None, alias='created_by')
    updatedBy: Optional[UserSimpleResponse] = Field(None, alias='updated_by')

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
