import uuid
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.mysql import CHAR
from typing import TYPE_CHECKING, List
from datetime import datetime

if TYPE_CHECKING:
    from .bia_impact_criteria import BIAImpactCriterion # type: ignore
    from .organizations import Organization # type: ignore
    from .users import User # type: ignore

from app.db.session import Base
from app.db.custom_types import SQLiteUUID


class BIACategory(Base):
    __tablename__ = "bia_categories"

    id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="bia_categories")
    bia_impact_criteria: Mapped[List["BIAImpactCriterion"]] = relationship("BIAImpactCriterion", back_populates="bia_category", cascade="all, delete-orphan")

    created_by_id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by_id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id], back_populates="bia_categories_created")
    updated_by: Mapped["User"] = relationship("User", foreign_keys=[updated_by_id], back_populates="bia_categories_updated")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Ensures that a BIA category name is unique within an organization
    __table_args__ = (UniqueConstraint('name', 'organization_id', name='uq_bia_category_name_organization'),)

    def __repr__(self):
        return f"<BIACategory(id={self.id}, name='{self.name}', organization_id='{self.organization_id}')>"
