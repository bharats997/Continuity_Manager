"""
BIA Impact Criteria Schemas
"""
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.domain.bia_impact_criteria import RatingTypeEnum
from .user_schemas import UserSimpleResponse as User

# BIA Impact Criterion Level Schemas
class BIAImpactCriterionLevelBase(BaseModel):
    level_name: Optional[str] = Field(None, max_length=255)
    level_value_min: Optional[float] = None
    level_value_max: Optional[float] = None
    quantitative_level_descriptor: Optional[str] = Field(None, max_length=255)
    score: int
    sequence_order: int

class BIAImpactCriterionLevelCreate(BIAImpactCriterionLevelBase):
    pass

class BIAImpactCriterionLevelUpdate(BIAImpactCriterionLevelBase):
    pass

class BIAImpactCriterionLevelInDBBase(BIAImpactCriterionLevelBase):
    id: UUID
    bia_impact_criterion_id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

class BIAImpactCriterionLevel(BIAImpactCriterionLevelInDBBase):
    pass

# BIA Impact Criterion Schemas
class BIAImpactCriterionBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    rating_type: RatingTypeEnum
    bia_category_id: UUID

class BIAImpactCriterionCreate(BIAImpactCriterionBase):
    levels: List[BIAImpactCriterionLevelCreate]

class BIAImpactCriterionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    rating_type: Optional[RatingTypeEnum] = None
    bia_category_id: Optional[UUID] = None
    levels: Optional[List[BIAImpactCriterionLevelUpdate]] = None

class BIAImpactCriterionInDBBase(BIAImpactCriterionBase):
    id: UUID
    organization_id: UUID
    created_by: Optional[User] = None
    updated_by: Optional[User] = None
    levels: List[BIAImpactCriterionLevel] = []

    class Config:
        from_attributes = True

class BIAImpactCriterion(BIAImpactCriterionInDBBase):
    pass

class BIAImpactCriterionResponse(BIAImpactCriterion):
    pass

class PaginatedBIAImpactCriteria(BaseModel):
    total: int
    page: int
    size: int
    results: List[BIAImpactCriterion]
