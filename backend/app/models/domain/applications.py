from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from backend.app.db.base_class import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    organizationId = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    appOwnerId = Column(Integer, ForeignKey("people.id"), nullable=True, index=True) # Person who owns/is responsible for the app
    
    applicationType = Column(String(100), nullable=True) # E.g., SaaS, Custom Developed, COTS
    hostingEnvironment = Column(String(100), nullable=True) # E.g., Cloud (AWS), On-Premise, Vendor Hosted
    criticality = Column(String(50), nullable=True) # E.g., High, Medium, Low (can be derived/updated via BIA later)

    isActive = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deletedAt = Column(DateTime(timezone=True), nullable=True)
    createdBy = Column(Integer, ForeignKey("people.id"), nullable=True)
    updatedBy = Column(Integer, ForeignKey("people.id"), nullable=True)
    deletedBy = Column(Integer, ForeignKey("people.id"), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="applications")
    appOwner = relationship("Person", foreign_keys=[appOwnerId], back_populates="owned_applications")
    
    creator = relationship("Person", foreign_keys=[createdBy])
    updater = relationship("Person", foreign_keys=[updatedBy])
    deleter = relationship("Person", foreign_keys=[deletedBy])
