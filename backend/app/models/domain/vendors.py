import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID # For PostgreSQL
from sqlalchemy.types import CHAR # Generic UUID type
from sqlalchemy.sql import func
from datetime import datetime

from ...db.session import Base
from ..vendor import VendorCriticality # Import the enum

if TYPE_CHECKING:
    from .organizations import Organization
    from .users import User

# Define a generic UUID type for SQLAlchemy
# This helps in being database-agnostic for UUIDs, though PG_UUID is often preferred for Postgres
# For SQLite, a CHAR(32) or custom type adapter is needed if native UUID is not supported well.
# Assuming a setup where UUIDs are handled (e.g., via a custom type like SQLiteUUID in other models)
# For simplicity, using CHAR(32) or letting the dialect handle it.
# Using the same SQLiteUUID pattern from other models for consistency:
from ...db.custom_types import SQLiteUUID # Using project's custom UUID type

class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # EmailStr validated at Pydantic level
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    service_provided: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criticality: Mapped[VendorCriticality] = mapped_column(SQLAlchemyEnum(VendorCriticality, name="vendor_criticality_enum"), default=VendorCriticality.MEDIUM)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, name="isActive")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), name="createdAt")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), name="updatedAt")
    # is_deleted and deleted_at for soft delete, if preferred over is_active alone
    # is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True, name="is_deleted")
    # deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), name="deleted_at", nullable=True)

    # Foreign Keys
    organization_id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), name="organizationId", index=True)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL", use_alter=True), name="createdBy", nullable=True)
    updated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL", use_alter=True), name="updatedBy", nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="vendors")
    created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_id], back_populates="created_vendors")
    updated_by: Mapped[Optional["User"]] = relationship(foreign_keys=[updated_by_id], back_populates="updated_vendors")

    def __repr__(self):
        return f"<Vendor(id={self.id}, name='{self.name}', organization_id={self.organization_id})>"
