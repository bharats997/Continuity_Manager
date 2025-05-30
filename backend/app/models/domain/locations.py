# backend/app/models/domain/locations.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ...database.session import Base # Corrected import path
from .departments import department_locations_association # Import association table

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state_province = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=False)
    
    organizationId = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    isActive = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Optional: Fields for tracking who created/updated the record
    # createdBy = Column(Integer, ForeignKey("people.id"), nullable=True)
    # updatedBy = Column(Integer, ForeignKey("people.id"), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="locations")
    people = relationship("Person", back_populates="location") # One location can have multiple people
    departments = relationship("Department", secondary=department_locations_association, back_populates="locations")

    def __repr__(self):
        return f"<Location(id={self.id}, name='{self.name}', organizationId={self.organizationId})>"
