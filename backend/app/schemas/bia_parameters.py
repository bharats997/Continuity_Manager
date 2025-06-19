from pydantic import BaseModel, ConfigDict, constr, conint
from typing import Optional, List, Union
from uuid import UUID
import datetime
from .user_audit import UserAuditInfo # Import the new schema

# Common Base Schema for audit fields (Read-only)
class AuditBase(BaseModel):
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None
    created_by: Optional[UserAuditInfo] = None # Changed from UUID
    updated_by: Optional[UserAuditInfo] = None # Changed from UUID

# BIA Impact Scale Level Schemas
class BIAImpactScaleLevelBase(BaseModel):
    level_value: conint(ge=1) # Ensure level value is positive
    level_name: constr(min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True

class BIAImpactScaleLevelCreate(BIAImpactScaleLevelBase):
    pass

class BIAImpactScaleLevelUpdate(BaseModel):
    level_value: Optional[conint(ge=1)] = None
    level_name: Optional[constr(min_length=1, max_length=255)] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class BIAImpactScaleLevelRead(BIAImpactScaleLevelBase, AuditBase):
    id: UUID
    organization_id: UUID # Added for multi-tenancy consistency
    impact_scale_id: UUID
    model_config = ConfigDict(from_attributes=True)

# BIA Impact Scale Schemas
class BIAImpactScaleBase(BaseModel):
    scale_name: constr(min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True

class BIAImpactScaleCreate(BIAImpactScaleBase):
    levels: List[BIAImpactScaleLevelCreate] = []

class BIAImpactScaleUpdate(BaseModel):
    scale_name: Optional[constr(min_length=1, max_length=255)] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    # For updating levels, it's often handled by dedicated endpoints or a more complex structure
    # For simplicity here, we'll allow adding new levels or expect full replacement if levels are provided.
    # A more robust approach might involve specific operations (add, remove, update) for levels.
    levels: Optional[List[Union[BIAImpactScaleLevelCreate, BIAImpactScaleLevelRead]]] = None # Allows sending existing level IDs or new level data

class BIAImpactScaleRead(BIAImpactScaleBase, AuditBase):
    id: UUID
    organization_id: UUID
    levels: List[BIAImpactScaleLevelRead] = []
    model_config = ConfigDict(from_attributes=True)

# BIA Timeframe Schemas
class BIATimeframeBase(BaseModel):
    timeframe_name: constr(min_length=1, max_length=255)
    sequence_order: conint(ge=0) # Ensure sequence order is non-negative
    description: Optional[str] = None
    is_active: bool = True

class BIATimeframeCreate(BIATimeframeBase):
    pass

class BIATimeframeUpdate(BaseModel):
    timeframe_name: Optional[constr(min_length=1, max_length=255)] = None
    sequence_order: Optional[conint(ge=0)] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class BIATimeframeRead(BIATimeframeBase, AuditBase):
    id: UUID
    organization_id: UUID
    model_config = ConfigDict(from_attributes=True)
