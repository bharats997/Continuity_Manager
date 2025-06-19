# backend/app/models/domain/locations.py
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey # Keep for now
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import TYPE_CHECKING, List, Optional

from ...db.session import Base
from ...db.custom_types import SQLiteUUID
from .departments import department_locations_association # Import association table
from .processes import process_locations_association # Import association table

if TYPE_CHECKING:
    from .organizations import Organization # type: ignore
    from .users import User # type: ignore
    from .departments import Department # type: ignore
    from .processes import Process # type: ignore

class Location(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    address_line1: Mapped[str] = mapped_column(String(255), name="address_line1")
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), name="address_line2", nullable=True)
    city: Mapped[str] = mapped_column(String(100))
    state_province: Mapped[Optional[str]] = mapped_column(String(100), name="state_province", nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), name="postal_code", nullable=True)
    country: Mapped[str] = mapped_column(String(100))
    
    is_active: Mapped[bool] = mapped_column(Boolean, name="isActive", default=True) # Default was True, nullable=False
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), name="createdAt", server_default=func.now()) # nullable=False implied
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), name="updatedAt", server_default=func.now(), onupdate=func.now()) # nullable=False implied
    
    # Foreign Keys
    organization_id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), name="organizationId", index=True) # nullable=False implied
    
    # Optional: Fields for tracking who created/updated the record
    # created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), name="createdBy", nullable=True, index=True)
    # updated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), name="updatedBy", nullable=True, index=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="locations")
    users: Mapped[List["User"]] = relationship(back_populates="location") # Renamed from people
    departments: Mapped[List["Department"]] = relationship(secondary=department_locations_association, back_populates="locations")

    # A location can be associated with multiple processes
    processes: Mapped[List["Process"]] = relationship(secondary=process_locations_association, back_populates="locations")

    def __repr__(self):
        return f"<Location(id={self.id}, name='{self.name}', organizationId={self.organization_id})>"
