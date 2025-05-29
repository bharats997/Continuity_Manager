# backend/app/models/domain/people.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ...database.session import Base # Assuming Base is in database.session
from .roles import Role # Assuming Role model is in roles.py
from .applications import Application # Import Application

# Association table for the many-to-many relationship between people and roles
people_roles_association = Table(
    'people_roles', Base.metadata,
    Column('personId', Integer, ForeignKey('people.id', ondelete="CASCADE"), primary_key=True),
    Column('roleId', Integer, ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True),
    Column('createdAt', DateTime(timezone=True), server_default=func.now())
)

class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organizationId = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    firstName = Column(String(100), nullable=False)
    lastName = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True) # Unique constraint (organizationId, email) handled at DB level
    departmentId = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    locationId = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True) # FR 1.5
    jobTitle = Column(String(100), nullable=True)
    isActive = Column(Boolean, default=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    createdBy = Column(Integer, ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    updatedBy = Column(Integer, ForeignKey("people.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="people")
    department = relationship("Department", foreign_keys="Person.departmentId", back_populates="people")
    location = relationship("Location", foreign_keys=[locationId], back_populates="people") # FR 1.5

    roles = relationship("Role", secondary=people_roles_association, back_populates="people") # M2M for roles

    owned_applications = relationship("Application", foreign_keys="[Application.appOwnerId]", back_populates="appOwner")

    # Self-referential relationships for createdBy and updatedBy if needed for ORM access
    # creator = relationship("Person", remote_side=[id], foreign_keys=[createdBy])
    # updater = relationship("Person", remote_side=[id], foreign_keys=[updatedBy])

# Add back_populates to Organization and Department models if they don't exist
# In Organization model: people = relationship("Person", back_populates="organization")
# In Department model: people = relationship("Person", back_populates="department")
