import enum
import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, ForeignKey, Enum, Integer, Float, DateTime, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.session import Base
from app.db.custom_types import SQLiteUUID

if TYPE_CHECKING:
    from .users import User
    from .organizations import Organization
    from .bia_categories import BIACategory
    from .bia_frameworks import BIAFrameworkParameter

class RatingTypeEnum(enum.Enum):
    QUALITATIVE = "QUALITATIVE"
    QUANTITATIVE = "QUANTITATIVE"

class BIAImpactCriterion(Base):

    __tablename__ = "bia_impact_criteria"

    id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    bia_category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bia_categories.id"), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating_type: Mapped[RatingTypeEnum] = mapped_column(Enum(RatingTypeEnum), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="bia_impact_criteria")
    bia_category: Mapped["BIACategory"] = relationship(back_populates="bia_impact_criteria")
    created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_id], back_populates="created_bia_impact_criteria")
    updated_by: Mapped[Optional["User"]] = relationship(foreign_keys=[updated_by_id], back_populates="updated_bia_impact_criteria")
    
    levels: Mapped[List["BIAImpactCriterionLevel"]] = relationship(back_populates="criterion", cascade="all, delete-orphan")

    # Relationship to framework parameters
    framework_associations: Mapped[List["BIAFrameworkParameter"]] = relationship(back_populates="criterion")

class BIAImpactCriterionLevel(Base):
    __tablename__ = "bia_impact_criterion_levels"

    id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bia_impact_criterion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bia_impact_criteria.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)

    level_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    level_value_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    level_value_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quantitative_level_descriptor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    score: Mapped[int] = mapped_column(Integer, nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    criterion: Mapped["BIAImpactCriterion"] = relationship(back_populates="levels")
    organization: Mapped["Organization"] = relationship(back_populates="bia_impact_criterion_levels")
    created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_id], back_populates="created_bia_impact_criterion_levels")
    updated_by: Mapped[Optional["User"]] = relationship(foreign_keys=[updated_by_id], back_populates="updated_bia_impact_criterion_levels")

