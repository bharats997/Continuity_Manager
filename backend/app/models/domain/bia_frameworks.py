import uuid
from sqlalchemy import Column, String, Text, Float, ForeignKey, Integer, Enum as SAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List
import enum

from app.db.session import Base
from app.models.domain.bia_impact_criteria import BIAImpactCriterion
from app.models.domain.users import User

class FormulaEnum(str, enum.Enum):
    WEIGHTED_AVERAGE = "WEIGHTED_AVERAGE"

class BIAFramework(Base):
    __tablename__ = "bia_frameworks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, index=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    formula: Mapped[FormulaEnum] = mapped_column(SAEnum(FormulaEnum), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)

    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    organization = relationship("Organization", back_populates="bia_frameworks")
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="bia_frameworks_created")
    updated_by = relationship("User", foreign_keys=[updated_by_id], back_populates="bia_frameworks_updated")

    parameters: Mapped[List["BIAFrameworkParameter"]] = relationship(back_populates="framework", cascade="all, delete-orphan")
    rtos: Mapped[List["BIAFrameworkRTO"]] = relationship(back_populates="framework", cascade="all, delete-orphan")

class BIAFrameworkParameter(Base):
    __tablename__ = "bia_framework_parameters"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, index=True, default=uuid.uuid4)
    framework_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bia_frameworks.id"), nullable=False)
    criterion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bia_impact_criteria.id"), nullable=False)
    weightage: Mapped[float] = mapped_column(Float, nullable=False)

    framework: Mapped["BIAFramework"] = relationship(back_populates="parameters")
    criterion: Mapped["BIAImpactCriterion"] = relationship(back_populates="framework_associations")

class BIAFrameworkRTO(Base):
    __tablename__ = "bia_framework_rtos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, index=True, default=uuid.uuid4)
    framework_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bia_frameworks.id"), nullable=False)
    display_text: Mapped[str] = mapped_column(String(100), nullable=False)
    value_in_hours: Mapped[int] = mapped_column(Integer, nullable=False)

    framework: Mapped["BIAFramework"] = relationship(back_populates="rtos")
