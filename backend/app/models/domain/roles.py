# backend/app/models/domain/roles.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ...database.session import Base # Assuming Base is in database.session
from .permissions import role_permissions_association # Import the association table

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationship to people
    people = relationship("Person", secondary="people_roles", back_populates="roles")

    # Relationship to permissions (many-to-many)
    permissions = relationship(
        "Permission",
        secondary=role_permissions_association,
        back_populates="roles"
    )
