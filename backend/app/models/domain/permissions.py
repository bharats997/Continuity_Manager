# backend/app/models/domain/permissions.py
import uuid
from sqlalchemy import Column, String, Text, Table, ForeignKey, DateTime
from ...db.custom_types import SQLiteUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ...db.session import Base # Assuming Base is in database.session

# Association table for Role and Permission many-to-many relationship
role_permissions_association = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', SQLiteUUID, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', SQLiteUUID, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
)

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(SQLiteUUID, primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True) # e.g., "department:create", "user:read"
    description = Column(Text, nullable=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to roles (many-to-many)
    roles = relationship(
        "Role",
        secondary=role_permissions_association,
        back_populates="permissions"
    )

    def __repr__(self):
        return f"<Permission(name='{self.name}')>"
