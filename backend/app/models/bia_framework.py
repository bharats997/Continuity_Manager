import enum
import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID # Alias to avoid conflict if uuid.UUID is used
from sqlalchemy.orm import Mapped, mapped_column, relationship # Keep for now, may become unused

# Removed: from ..database.session import Base
# Removed: from .mixins import TimestampMixin


class RatingType(str, enum.Enum):
    QUALITATIVE = "Qualitative"
    QUANTITATIVE = "Quantitative"


# Removed BIAImpactScale, BIAImpactScaleLevel, BIATimeframe SQLAlchemy model definitions


# --- Pydantic Schemas ---


class BIAImpactScaleLevelBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    min_range: Optional[float] = None
    max_range: Optional[float] = None
    score: int


class BIAImpactScaleLevelCreate(BIAImpactScaleLevelBase):
    pass


class BIAImpactScaleLevelUpdate(BIAImpactScaleLevelBase):
    id: Optional[uuid.UUID] = None


class BIAImpactScaleLevelResponse(BIAImpactScaleLevelBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class BIAImpactScaleBase(BaseModel):
    name: str
    description: Optional[str] = None
    rating_type: RatingType


class BIAImpactScaleCreate(BIAImpactScaleBase):
    levels: List[BIAImpactScaleLevelCreate]


class BIAImpactScaleUpdate(BIAImpactScaleBase):
    levels: Optional[List[BIAImpactScaleLevelUpdate]] = None


class BIAImpactScaleResponse(BIAImpactScaleBase):
    id: uuid.UUID
    levels: List[BIAImpactScaleLevelResponse]

    model_config = ConfigDict(from_attributes=True)


class BIATimeframeBase(BaseModel):
    name: str
    description: Optional[str] = None
    sequence: int


class BIATimeframeCreate(BIATimeframeBase):
    pass


class BIATimeframeUpdate(BIATimeframeBase):
    pass


class BIATimeframeResponse(BIATimeframeBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
