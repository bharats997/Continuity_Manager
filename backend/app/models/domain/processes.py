# backend/app/models/domain/processes.py
import uuid
import enum
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum as SAEnum, Text, Integer, DateTime, Table, UniqueConstraint, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import TYPE_CHECKING, Optional, List

from ...db.session import Base
from ...db.custom_types import SQLiteUUID

if TYPE_CHECKING:
    from .users import User  # type: ignore
    from .departments import Department  # type: ignore
    from .locations import Location  # type: ignore
    from .applications import Application  # type: ignore

from .applications import process_applications_association # For relationship

# Association table for Process and Location (Many-to-Many)
process_locations_association = Table(
    'process_locations',
    Base.metadata,
    Column('process_id', SQLiteUUID(as_uuid=True), ForeignKey('processes.id'), primary_key=True),
    Column('location_id', SQLiteUUID(as_uuid=True), ForeignKey('locations.id'), primary_key=True)
)



# Association table for Process dependencies (Self-referential Many-to-Many)
process_dependencies_association = Table(
    'process_dependencies',
    Base.metadata,
    Column('upstream_process_id', SQLiteUUID(as_uuid=True), ForeignKey('processes.id'), primary_key=True),
    Column('downstream_process_id', SQLiteUUID(as_uuid=True), ForeignKey('processes.id'), primary_key=True)
)

class Process(Base):
    __tablename__ = "processes"

    id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sla: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tat: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Turnaround Time
    seasonality: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    peak_times: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    num_team_members: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rto: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rpo: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    criticality_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Foreign Keys
    department_id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey('departments.id'), nullable=False)
    process_owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    # Relationships
    department: Mapped["Department"] = relationship(back_populates="processes")
    process_owner: Mapped[Optional["User"]] = relationship(foreign_keys=[process_owner_id], back_populates="owned_processes")

    locations: Mapped[List["Location"]] = relationship(secondary=process_locations_association, back_populates="processes")
    applications_used: Mapped[List["Application"]] = relationship(secondary=process_applications_association, back_populates="processes")

    # Self-referential many-to-many for dependencies
    # A process can have multiple upstream processes (processes it depends on)
    upstream_dependencies: Mapped[List["Process"]] = relationship(
        secondary=process_dependencies_association,
        primaryjoin=id == process_dependencies_association.c.downstream_process_id,
        secondaryjoin=id == process_dependencies_association.c.upstream_process_id,
        back_populates="downstream_dependencies"
    )
    # A process can have multiple downstream processes (processes that depend on it)
    downstream_dependencies: Mapped[List["Process"]] = relationship(
        secondary=process_dependencies_association,
        primaryjoin=id == process_dependencies_association.c.upstream_process_id,
        secondaryjoin=id == process_dependencies_association.c.downstream_process_id,
        back_populates="upstream_dependencies"
    )

    # Audit fields
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id", use_alter=True, name="fk_process_created_by"), nullable=True)
    updated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id", use_alter=True, name="fk_process_updated_by"), nullable=True)

    created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_id], back_populates="created_processes")
    updated_by: Mapped[Optional["User"]] = relationship(foreign_keys=[updated_by_id], back_populates="updated_processes")

    __table_args__ = (UniqueConstraint('name', 'department_id', name='_process_name_department_uc'),)

    def __repr__(self):
        return f"<Process(id={self.id}, name='{self.name}')>"

    @property
    def organization_id(self) -> Optional[uuid.UUID]:
        """Derives organization_id from the associated department."""
        if self.department:
            return self.department.organization_id
        return None
