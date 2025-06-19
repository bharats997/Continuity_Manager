import uuid
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.sql import func
from sqlalchemy import UUID # Use generic UUID for cross-DB compatibility

class TimestampMixin:
    """Adds created_at and updated_at columns to a model."""
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

class UserTrackedMixin:
    """Adds created_by_id and updated_by_id foreign keys to a model."""
    @declared_attr
    def created_by_id(cls):
        return Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    @declared_attr
    def updated_by_id(cls):
        return Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    @declared_attr
    def created_by(cls):
        return relationship("User", foreign_keys=[cls.created_by_id], backref=f'created_{cls.__tablename__}')

    @declared_attr
    def updated_by(cls):
        return relationship("User", foreign_keys=[cls.updated_by_id], backref=f'updated_{cls.__tablename__}')

class OrganizationMixin:
    """Adds organization_id foreign key to a model."""
    @declared_attr
    def organization_id(cls):
        return Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)

    @declared_attr
    def organization(cls):
        return relationship("Organization", foreign_keys=[cls.organization_id])
