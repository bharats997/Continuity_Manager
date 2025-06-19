import uuid
import enum
from sqlalchemy import Table, Column, String, Boolean, ForeignKey, Enum as SAEnum, Text, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import TYPE_CHECKING, Optional, List

# Ensure relative imports are correct based on your project structure
from ...db.session import Base
from ...db.custom_types import SQLiteUUID 


# Association table for Process and Application (Many-to-Many)
process_applications_association = Table(
    'process_applications',
    Base.metadata,
    Column('process_id', SQLiteUUID(as_uuid=True), ForeignKey('processes.id'), primary_key=True),
    Column('application_id', SQLiteUUID(as_uuid=True), ForeignKey('applications.id'), primary_key=True)
)

if TYPE_CHECKING:
    from .organizations import Organization # type: ignore
    from .users import User # type: ignore # As per PRD FR 1.2 and FR 1.4
    from .processes import Process # type: ignore # For future process_applications relationship

class ApplicationStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class ApplicationType(str, enum.Enum):
    SAAS = "SaaS"
    OWNED = "Owned"

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Added for general utility, not in PRD table but good practice
    type: Mapped[ApplicationType] = mapped_column(SAEnum(ApplicationType, name="application_type_enum", create_constraint=True), nullable=False)
    hosted_on: Mapped[Optional[str]] = mapped_column(String(255), name="hostedOn", nullable=True) # As per PRD: hostedOn (VARCHAR)
    workarounds: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # As per PRD: workarounds (TEXT)
    derived_rto: Mapped[Optional[str]] = mapped_column(String(50), name="derivedRTO", nullable=True) # As per PRD: derivedRTO (VARCHAR, nullable)
    status: Mapped[ApplicationStatusEnum] = mapped_column(SAEnum(ApplicationStatusEnum, name="application_status_enum", create_constraint=True, values_callable=lambda x: [e.value for e in x]), default=ApplicationStatusEnum.ACTIVE, nullable=False)
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # Matches Pydantic ApplicationBase
    vendor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Matches Pydantic ApplicationBase
    criticality: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # Matches Pydantic model

    organization_id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("organizations.id"), name="organizationId", nullable=False) # As per PRD
    app_owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id"), name="appOwnerId", nullable=True) # As per PRD: appOwnerId (FK to users.id, nullable)

    # Relationships
    organization: Mapped["Organization"] = relationship(foreign_keys=[organization_id], back_populates="applications")
    app_owner: Mapped[Optional["User"]] = relationship(foreign_keys=[app_owner_id], back_populates="owned_applications")

    # Audit fields
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), name="createdAt", server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), name="updatedAt", server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id", name="fk_application_created_by", use_alter=True, ondelete="SET NULL"), name="createdById", nullable=True)
    updated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id", name="fk_application_updated_by", use_alter=True, ondelete="SET NULL"), name="updatedById", nullable=True)

    created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_id], back_populates="created_applications")
    updated_by: Mapped[Optional["User"]] = relationship(foreign_keys=[updated_by_id], back_populates="updated_applications")

    # Relationship to processes (Many-to-Many)
    processes: Mapped[List["Process"]] = relationship(
        secondary=process_applications_association,
        back_populates="applications_used" # Corresponds to 'applications_used' in Process model
    )

    __table_args__ = (UniqueConstraint('name', 'organizationId', name='_application_name_organization_uc'),) # As per PRD: name (VARCHAR, UNIQUE per organization)

    def __repr__(self):
        return f"<Application(id={self.id}, name='{self.name}', organization_id='{self.organization_id}')>"
