# backend/app/models/domain/users.py
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column # Using Mapped for consistency
from sqlalchemy.sql import func
from typing import TYPE_CHECKING, Optional, List # List was already used in Mapped[list[]]

# Ensure relative imports are correct based on your project structure
from app.db.session import Base
from app.db.custom_types import SQLiteUUID

if TYPE_CHECKING:
    from .organizations import Organization # type: ignore
    from .departments import Department # type: ignore
    from .locations import Location # type: ignore
    from .applications import Application # For created_by/updated_by relationships
    from .processes import Process # For created_by/updated_by relationships
    from .vendors import Vendor # For created_by/updated_by relationships
    from .roles import Role # type: ignore
    from .bia_parameters import BIAImpactScale, BIAImpactScaleLevel, BIATimeframe # type: ignore
    from .bia_impact_criteria import BIAImpactCriterion # type: ignore
    from app.models.domain.bia_categories import BIACategory
    from app.models.domain.bia_frameworks import BIAFramework # type: ignore

# Association table for the many-to-many relationship between users and roles
user_roles_association = Table(
    'user_roles', Base.metadata,
    Column('user_id', SQLiteUUID(as_uuid=True), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('role_id', SQLiteUUID(as_uuid=True), ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)

class User(Base): # Renamed from Person
    __tablename__ = "users" # Renamed from people

    id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    first_name: Mapped[str] = mapped_column(String(100), name="firstName") # PRD: firstName
    last_name: Mapped[str] = mapped_column(String(100), name="lastName")   # PRD: lastName
    email: Mapped[str] = mapped_column(String(255), index=True) # PRD: email (UNIQUE per organization - needs composite unique constraint)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), name="passwordHash", nullable=True) # PRD: passwordHash - To be added from FR 1.2
    job_title: Mapped[Optional[str]] = mapped_column(String(100), name="jobTitle", nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, name="isActive", default=True) # PRD: isActive
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), name="createdAt", server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), name="updatedAt", default=func.now(), onupdate=func.now())
    
    # Foreign Keys
    organization_id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), name="organizationId", index=True) # PRD: organizationId
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL", use_alter=True), name="departmentId", nullable=True, index=True) # PRD: departmentId
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), name="locationId", nullable=True, index=True) # PRD: locationId
    
    # created_by_id: Mapped[uuid.UUID | None] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL", use_alter=True), name="createdBy", nullable=True, index=True)
    # updated_by_id: Mapped[uuid.UUID | None] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL", use_alter=True), name="updatedBy", nullable=True, index=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="users") # Organization model needs 'users' relationship
    department: Mapped[Optional["Department"]] = relationship(foreign_keys=[department_id], back_populates="users") # Department model needs 'users'
    location: Mapped[Optional["Location"]] = relationship(foreign_keys=[location_id], back_populates="users") # Location model needs 'users'

    roles: Mapped[List["Role"]] = relationship(secondary=user_roles_association, back_populates="users") # Role model needs 'users'

    # Applications owned by this user
    owned_applications: Mapped[List["Application"]] = relationship(foreign_keys="[Application.app_owner_id]", back_populates="app_owner")
    created_applications: Mapped[List["Application"]] = relationship(foreign_keys="[Application.created_by_id]", back_populates="created_by")
    updated_applications: Mapped[List["Application"]] = relationship(foreign_keys="[Application.updated_by_id]", back_populates="updated_by")
    
    # Departments headed by this user
    headed_departments: Mapped[List["Department"]] = relationship(foreign_keys="[Department.department_head_id]", back_populates="department_head")

    # Processes related to this user
    owned_processes: Mapped[List["Process"]] = relationship(foreign_keys="[Process.process_owner_id]", back_populates="process_owner")
    created_processes: Mapped[List["Process"]] = relationship(foreign_keys="[Process.created_by_id]", back_populates="created_by")
    updated_processes: Mapped[List["Process"]] = relationship(foreign_keys="[Process.updated_by_id]", back_populates="updated_by")

    created_bia_impact_scales: Mapped[List["BIAImpactScale"]] = relationship(foreign_keys="[BIAImpactScale.created_by_id]", back_populates="created_by")
    updated_bia_impact_scales: Mapped[List["BIAImpactScale"]] = relationship(foreign_keys="[BIAImpactScale.updated_by_id]", back_populates="updated_by")
    created_bia_impact_scale_levels: Mapped[List["BIAImpactScaleLevel"]] = relationship(foreign_keys="[BIAImpactScaleLevel.created_by_id]", back_populates="created_by")
    updated_bia_impact_scale_levels: Mapped[List["BIAImpactScaleLevel"]] = relationship(foreign_keys="[BIAImpactScaleLevel.updated_by_id]", back_populates="updated_by")
    created_bia_timeframes: Mapped[List["BIATimeframe"]] = relationship(foreign_keys="[BIATimeframe.created_by_id]", back_populates="created_by")
    updated_bia_timeframes: Mapped[List["BIATimeframe"]] = relationship(foreign_keys="[BIATimeframe.updated_by_id]", back_populates="updated_by")

    created_bia_impact_criterion_levels: Mapped[List["BIAImpactCriterionLevel"]] = relationship(foreign_keys="[BIAImpactCriterionLevel.created_by_id]", back_populates="created_by")
    updated_bia_impact_criterion_levels: Mapped[List["BIAImpactCriterionLevel"]] = relationship(foreign_keys="[BIAImpactCriterionLevel.updated_by_id]", back_populates="updated_by")

    created_vendors: Mapped[List["Vendor"]] = relationship(foreign_keys="[Vendor.created_by_id]", back_populates="created_by")
    updated_vendors: Mapped[List["Vendor"]] = relationship(foreign_keys="[Vendor.updated_by_id]", back_populates="updated_by")

    created_bia_impact_criteria: Mapped[List["BIAImpactCriterion"]] = relationship(foreign_keys="[BIAImpactCriterion.created_by_id]", back_populates="created_by")
    updated_bia_impact_criteria: Mapped[List["BIAImpactCriterion"]] = relationship(foreign_keys="[BIAImpactCriterion.updated_by_id]", back_populates="updated_by")

    # BIACategory relationships
    bia_categories_created: Mapped[List["BIACategory"]] = relationship(foreign_keys="[BIACategory.created_by_id]", back_populates="created_by")
    bia_categories_updated: Mapped[List["BIACategory"]] = relationship(foreign_keys="[BIACategory.updated_by_id]", back_populates="updated_by")

    # Relationships for BIAFramework
    bia_frameworks_created: Mapped[List["BIAFramework"]] = relationship(foreign_keys="[BIAFramework.created_by_id]", back_populates="created_by")
    bia_frameworks_updated: Mapped[List["BIAFramework"]] = relationship(foreign_keys="[BIAFramework.updated_by_id]", back_populates="updated_by")

    __table_args__ = (UniqueConstraint('email', 'organizationId', name='_user_email_organization_uc'),) # For PRD: email UNIQUE per organization

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"

# Comments for related model updates:
# In Organization model: users: Mapped[list["User"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
# In Department model: 
#   department_head_id: Mapped[uuid.UUID | None] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
#   department_head: Mapped["User | None"] = relationship(foreign_keys=[department_head_id], back_populates="headed_departments")
#   users: Mapped[list["User"]] = relationship(foreign_keys="[User.department_id]", back_populates="department")
# In Location model: users: Mapped[list["User"]] = relationship(back_populates="location")
# In Role model: users: Mapped[list["User"]] = relationship(secondary=user_roles_association, back_populates="roles")
