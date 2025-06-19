import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import TYPE_CHECKING, List, Optional

from ...db.session import Base
from ...db.custom_types import SQLiteUUID

if TYPE_CHECKING:
    from .organizations import Organization
    from .users import User
    from .bia_impact_scale_levels import BIAImpactScaleLevel

class BIAImpactScale(Base):
    __tablename__ = "bia_impact_scales"

    id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    scale_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Foreign Keys
    organization_id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="bia_impact_scales")
    created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_id])
    updated_by: Mapped[Optional["User"]] = relationship(foreign_keys=[updated_by_id])
    levels: Mapped[List["BIAImpactScaleLevel"]] = relationship(back_populates="impact_scale", cascade="all, delete-orphan")
