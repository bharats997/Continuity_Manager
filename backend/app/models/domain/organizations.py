# backend/app/models/domain/organizations.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database.session import Base
from .applications import Application

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    industry = Column(String(100), nullable=True)
    isActive = Column(Boolean, default=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")
    people = relationship("Person", back_populates="organization", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="organization", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="organization", cascade="all, delete-orphan")
    # Add other relationships as needed, e.g., assets, etc.

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"
