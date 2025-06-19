# backend/app/schemas/processes.py
import uuid
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# Assuming user_schemas.py, department.py, location.py, applications.py are in the same 'schemas' directory
from .user_schemas import UserSimpleResponse # UserSchema as UserResponse was used before, check if UserResponse is needed or UserSimpleResponse is enough for created_by/updated_by
from .department import DepartmentSimpleResponse # Assuming department.py contains DepartmentSimpleResponse
from .location import LocationSchema as LocationResponse # Assuming location.py contains LocationSchema
from .applications import ApplicationRead as ApplicationResponse # Corrected import

class ProcessBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the business process")
    description: Optional[str] = Field(None, description="Detailed description of the business process")
    sla: Optional[str] = Field(None, max_length=255, description="Service Level Agreement")
    tat: Optional[str] = Field(None, max_length=255, description="Turnaround Time")
    seasonality: Optional[str] = Field(None, max_length=255, description="Seasonality of the process (e.g., Monthly, Quarterly, Year-End)")
    peak_times: Optional[str] = Field(None, max_length=255, description="Peak operational times for the process")
    frequency: Optional[str] = Field(None, max_length=255, description="Frequency of process execution (e.g., Daily, Weekly)")
    num_team_members: Optional[int] = Field(None, ge=0, description="Number of team members involved in the process")
    organization_id: uuid.UUID = Field(..., description="ID of the organization this process belongs to")
    department_id: uuid.UUID = Field(..., description="ID of the department this process belongs to")
    process_owner_id: Optional[uuid.UUID] = Field(None, description="ID of the user who owns this process")
    rto: Optional[float] = Field(None, ge=0, description="Recovery Time Objective in hours")
    rpo: Optional[float] = Field(None, ge=0, description="Recovery Point Objective in hours")
    criticality_level: Optional[str] = Field(None, max_length=50, description="Criticality level of the process (e.g., High, Medium, Low)")

class ProcessCreate(ProcessBase):
    location_ids: Optional[List[uuid.UUID]] = Field(default_factory=list, description="List of location IDs associated with this process")
    application_ids: Optional[List[uuid.UUID]] = Field(default_factory=list, description="List of application IDs used by this process")
    upstream_dependency_ids: Optional[List[uuid.UUID]] = Field(default_factory=list, description="List of upstream process IDs this process depends on")
    downstream_dependency_ids: Optional[List[uuid.UUID]] = Field(default_factory=list, description="List of downstream process IDs that depend on this process")

class ProcessUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="New name for the business process")
    description: Optional[str] = Field(None, description="New detailed description for the business process")
    sla: Optional[str] = Field(None, max_length=255, description="New Service Level Agreement")
    tat: Optional[str] = Field(None, max_length=255, description="New Turnaround Time")
    seasonality: Optional[str] = Field(None, max_length=255, description="New seasonality of the process")
    peak_times: Optional[str] = Field(None, max_length=255, description="New peak operational times for the process")
    frequency: Optional[str] = Field(None, max_length=255, description="New frequency of process execution")
    num_team_members: Optional[int] = Field(None, ge=0, description="New number of team members involved")
    department_id: Optional[uuid.UUID] = Field(None, description="New ID of the department this process belongs to.")
    process_owner_id: Optional[uuid.UUID] = Field(None, description="New ID of the user who owns this process")
    location_ids: Optional[List[uuid.UUID]] = Field(None, description="New list of location IDs. Replaces existing.")
    application_ids: Optional[List[uuid.UUID]] = Field(None, description="New list of application IDs. Replaces existing.")
    upstream_dependency_ids: Optional[List[uuid.UUID]] = Field(None, description="New list of upstream process IDs. Replaces existing.")
    downstream_dependency_ids: Optional[List[uuid.UUID]] = Field(None, description="New list of downstream process IDs. Replaces existing.")

class ProcessResponseSimple(BaseModel):
    id: uuid.UUID
    name: str
    model_config = ConfigDict(from_attributes=True)

class ProcessResponse(ProcessBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UserSimpleResponse] = None
    updated_by: Optional[UserSimpleResponse] = None
    department: Optional[DepartmentSimpleResponse] = None
    process_owner: Optional[UserSimpleResponse] = None
    locations: List[LocationResponse] = Field(default_factory=list)
    applications_used: List[ApplicationResponse] = Field(default_factory=list)
    upstream_dependencies: List[ProcessResponseSimple] = Field(default_factory=list)
    downstream_dependencies: List[ProcessResponseSimple] = Field(default_factory=list)
    is_active: bool = Field(True, description="Indicates if the process is active")
    # is_deleted and deleted_at from old model are represented by is_active for consistency
    model_config = ConfigDict(from_attributes=True)

class ProcessListResponse(BaseModel):
    items: List[ProcessResponse]
    total: int
    page: int
    size: int
