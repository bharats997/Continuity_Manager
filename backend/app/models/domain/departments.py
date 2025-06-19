# backend/app/models/domain/departments.py
import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Table, Integer # Keep for now
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import TYPE_CHECKING, List, Optional

from app.db.session import Base
from app.db.custom_types import SQLiteUUID

if TYPE_CHECKING:
    from .organizations import Organization # type: ignore
    from .users import User # type: ignore
    from .locations import Location # type: ignore
    from .processes import Process # type: ignore

# Association table for Department and Location (Many-to-Many)
department_locations_association = Table(
    'department_locations_association',
    Base.metadata,
    Column('department_id', SQLiteUUID(as_uuid=True), ForeignKey('departments.id', ondelete="CASCADE"), primary_key=True),
    Column('location_id', SQLiteUUID(as_uuid=True), ForeignKey('locations.id', ondelete="CASCADE"), primary_key=True)
)

class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, name="isActive", default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), name="createdAt", server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), name="updatedAt", default=func.now(), onupdate=func.now())
    number_of_team_members: Mapped[Optional[int]] = mapped_column(Integer, name="number_of_team_members", nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True, name="is_deleted") # name added for consistency
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), name="deleted_at", nullable=True)

    # Foreign Keys
    # organization_id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), name="organizationId", index=True)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL", use_alter=True), name="createdBy", nullable=True) # Changed to users.id
    updated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL", use_alter=True), name="updatedBy", nullable=True) # Changed to users.id
    department_head_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL", use_alter=True), nullable=True) # Changed to users.id

    # Relationships
    # organization: Mapped["Organization"] = relationship(back_populates="departments")
    
    # A department can have multiple users
    users: Mapped[List["User"]] = relationship(foreign_keys="[User.department_id]", back_populates="department") # Specify FK on User model
    
    # A department has one head, who is a User
    department_head: Mapped[Optional["User"]] = relationship(foreign_keys=[department_head_id], back_populates="headed_departments")

    locations: Mapped[List["Location"]] = relationship(
        secondary=department_locations_association,
        back_populates="departments"
    )

    # A department can have multiple processes
    processes: Mapped[List["Process"]] = relationship(back_populates="department", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}', organization_id={self.organization_id})>"
