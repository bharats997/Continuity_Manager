# backend/app/models/department.py
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from .person import Person  # For Department Head details in response
from .location import Location  # For Location details in response

# Base model for common department attributes
class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the department")
    description: Optional[str] = Field(None, max_length=1000, description="Detailed description of the department")
    organizationId: int = Field(..., gt=0, description="ID of the organization this department belongs to")
    department_head_id: Optional[int] = Field(None, foreign_key="people.id", description="ID of the department head (Person)")
    number_of_team_members: Optional[int] = Field(None, gt=0, description="Number of team members in the department")

# Model for creating a new department
class DepartmentCreate(DepartmentBase):
    location_ids: List[int] = Field(default_factory=list, description="List of Location IDs associated with the department")

# Model for updating an existing department
class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    department_head_id: Optional[int] = Field(None, foreign_key="people.id")
    location_ids: Optional[List[int]] = None
    number_of_team_members: Optional[int] = Field(None, gt=0)
    isActive: Optional[bool] = None # Allow updating active status

# Model for department response (what's sent back via API)
class DepartmentResponse(DepartmentBase):
    id: int = Field(..., gt=0, description="Unique ID of the department")
    isActive: bool = Field(..., description="Whether the department is currently active")
    createdAt: datetime = Field(..., description="Timestamp of department creation")
    updatedAt: datetime = Field(..., description="Timestamp of last department update")
    # createdBy: Optional[int] = Field(None, description="ID of the user who created the department") # If tracking users
    # updatedBy: Optional[int] = Field(None, description="ID of the user who last updated the department") # If tracking users

    department_head: Optional[Person] = Field(None, description="Department head details")
    locations: List[Location] = Field(default_factory=list, description="List of associated locations")
    is_deleted: bool = Field(False, description="Whether the department is soft-deleted")
    deleted_at: Optional[datetime] = Field(None, description="Timestamp of soft deletion")

    model_config = ConfigDict(from_attributes=True)  # Pydantic V2 compatibility

# For listing multiple departments
class DepartmentListResponse(BaseModel):
    departments: List[DepartmentResponse]
    total: int
