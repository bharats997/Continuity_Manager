# backend/app/models/domain/organizations.py
import uuid
from sqlalchemy import Column, String, DateTime, Text, Boolean # Keep existing imports if used by other models not yet converted
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import TYPE_CHECKING, List, Optional

# Ensure relative imports are correct
from app.db.session import Base
from app.db.custom_types import SQLiteUUID

if TYPE_CHECKING:
    from .bia_impact_scales import BIAImpactScale
    from .bia_timeframes import BIATimeframe
    from .departments import Department # type: ignore
    from .users import User # type: ignore # Changed from Person
    from .locations import Location # type: ignore
    from .applications import Application # type: ignore
    from .vendors import Vendor # type: ignore
    from .roles import Role # type: ignore
    from .bia_impact_criteria import BIAImpactCriterion, BIAImpactCriterionLevel # type: ignore
    from .bia_categories import BIACategory # type: ignore
    from .bia_frameworks import BIAFramework # type: ignore

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, name="isActive", default=True) # Mapped to existing isActive
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), name="createdAt", server_default=func.now()) # Mapped to existing createdAt
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), name="updatedAt", default=func.now(), onupdate=func.now()) # Mapped to existing updatedAt

    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    locations: Mapped[List["Location"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    applications: Mapped[List["Application"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    vendors: Mapped[List["Vendor"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    roles: Mapped[List["Role"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    bia_categories: Mapped[List["BIACategory"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    bia_timeframes: Mapped[List["BIATimeframe"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    bia_impact_scales: Mapped[List["BIAImpactScale"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    bia_impact_criteria: Mapped[List["BIAImpactCriterion"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    bia_impact_criterion_levels: Mapped[List["BIAImpactCriterionLevel"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    bia_frameworks: Mapped[List["BIAFramework"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    # departments: Mapped[List["Department"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"
