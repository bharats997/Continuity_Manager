# backend/app/models/domain/departments.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ...database.session import Base # Assuming Base is in database.session

# Association table for Department and Location (Many-to-Many)
department_locations_association = Table(
    'department_locations_association',
    Base.metadata,
    Column('department_id', Integer, ForeignKey('departments.id', ondelete="CASCADE"), primary_key=True),
    Column('location_id', Integer, ForeignKey('locations.id', ondelete="CASCADE"), primary_key=True)
)

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organizationId = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    isActive = Column(Boolean, default=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    createdBy = Column(Integer, ForeignKey("people.id", ondelete="SET NULL", use_alter=True), nullable=True)
    updatedBy = Column(Integer, ForeignKey("people.id", ondelete="SET NULL", use_alter=True), nullable=True)
    department_head_id = Column(Integer, ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    number_of_team_members = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="departments")
    people = relationship("Person", foreign_keys="Person.departmentId", back_populates="department") # A department can have multiple people
    department_head = relationship("Person", foreign_keys=[department_head_id], back_populates="headed_departments") # Changed to allow back_populates

    locations = relationship(
        "Location",
        secondary=department_locations_association,
        back_populates="departments"
    )

    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}', organization_id={self.organizationId})>"
