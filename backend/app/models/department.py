# backend/app/models/department.py
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# Base model for common department attributes
class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the department")
    description: Optional[str] = Field(None, max_length=1000, description="Detailed description of the department")
    organizationId: int = Field(..., gt=0, description="ID of the organization this department belongs to")

# Model for creating a new department
class DepartmentCreate(DepartmentBase):
    pass

# Model for updating an existing department
class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    isActive: Optional[bool] = None # Allow updating active status

# Model for department response (what's sent back via API)
class DepartmentResponse(DepartmentBase):
    id: int = Field(..., gt=0, description="Unique ID of the department")
    isActive: bool = Field(..., description="Whether the department is currently active")
    createdAt: datetime = Field(..., description="Timestamp of department creation")
    updatedAt: datetime = Field(..., description="Timestamp of last department update")
    # createdBy: Optional[int] = Field(None, description="ID of the user who created the department") # If tracking users
    # updatedBy: Optional[int] = Field(None, description="ID of the user who last updated the department") # If tracking users

    model_config = ConfigDict(from_attributes=True)  # Pydantic V2 compatibility

# For listing multiple departments
class DepartmentListResponse(BaseModel):
    departments: List[DepartmentResponse]
    total: int
