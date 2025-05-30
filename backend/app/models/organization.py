# backend/app/models/organization.py
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# Forward references for relationships that might be included later
# from .department import DepartmentResponse
# from .person import Person # Assuming Person is the Pydantic model for response
# from .location import LocationResponse
# from .application import ApplicationResponse # Circular dependency if full model is used, handle carefully

class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    industry: Optional[str] = Field(None, max_length=100)
    isActive: bool = True

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    industry: Optional[str] = Field(None, max_length=100)
    isActive: Optional[bool] = None

class OrganizationResponse(OrganizationBase):
    id: int
    createdAt: datetime
    updatedAt: datetime

    # Example of how related items might be included in a full response.
    # For now, keeping it simple to avoid circular dependencies with ApplicationResponse.
    # departments: List[DepartmentResponse] = []
    # people: List[Person] = [] 
    # locations: List[LocationResponse] = []
    # applications: List[ApplicationResponse] = [] # This would require careful handling of circular imports

    model_config = ConfigDict(from_attributes=True)
