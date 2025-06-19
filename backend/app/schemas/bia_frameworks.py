import uuid
from typing import List, Optional
from pydantic import BaseModel, Field, validator

from app.models.domain.bia_frameworks import FormulaEnum

# Schema for RTO options within a framework
class BIAFrameworkRTOBase(BaseModel):
    display_text: str = Field(..., max_length=100)
    value_in_hours: int

class BIAFrameworkRTOCreate(BIAFrameworkRTOBase):
    pass

class BIAFrameworkRTO(BIAFrameworkRTOBase):
    id: uuid.UUID

    class Config:
        from_attributes = True

# Schema for parameters within a framework
class BIAFrameworkParameterBase(BaseModel):
    criterion_id: uuid.UUID
    weightage: float = Field(..., gt=0, le=100)

class BIAFrameworkParameterCreate(BIAFrameworkParameterBase):
    pass

class BIAFrameworkParameter(BIAFrameworkParameterBase):
    id: uuid.UUID

    class Config:
        from_attributes = True

# Base schema for the BIA Framework
class BIAFrameworkBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    formula: FormulaEnum = FormulaEnum.WEIGHTED_AVERAGE
    threshold: float

# Schema for creating a BIA Framework
class BIAFrameworkCreate(BIAFrameworkBase):
    parameters: List[BIAFrameworkParameterCreate]
    rtos: List[BIAFrameworkRTOCreate]

    @validator('parameters')
    def weightages_must_sum_to_100(cls, v):
        total_weightage = sum(p.weightage for p in v)
        if not (99.99 <= total_weightage <= 100.01): # Allow for floating point inaccuracies
            raise ValueError('The sum of all parameter weightages must be 100.')
        return v

# Schema for updating a BIA Framework
class BIAFrameworkUpdate(BIAFrameworkBase):
    name: Optional[str] = Field(None, max_length=255)
    threshold: Optional[float] = None
    parameters: Optional[List[BIAFrameworkParameterCreate]] = None
    rtos: Optional[List[BIAFrameworkRTOCreate]] = None

    @validator('parameters')
    def update_weightages_must_sum_to_100(cls, v):
        if v is not None:
            total_weightage = sum(p.weightage for p in v)
            if not (99.99 <= total_weightage <= 100.01):
                raise ValueError('The sum of all parameter weightages must be 100.')
        return v

# Schema for reading a BIA Framework (e.g., from API response)
class BIAFrameworkInDBBase(BIAFrameworkBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_by_id: uuid.UUID
    updated_by_id: uuid.UUID

    class Config:
        from_attributes = True

class BIAFramework(BIAFrameworkInDBBase):
    parameters: List[BIAFrameworkParameter]
    rtos: List[BIAFrameworkRTO]
