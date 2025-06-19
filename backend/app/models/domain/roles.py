# backend/app/models/domain/roles.py
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey # Keep for now
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import TYPE_CHECKING, List, Optional

from ...db.session import Base
from ...db.custom_types import SQLiteUUID
from .permissions import role_permissions_association # Import the association table for permissions
from .users import user_roles_association # Import the association table for users

if TYPE_CHECKING:
    from .users import User # type: ignore
    from .permissions import Permission # type: ignore
    from .organizations import Organization # type: ignore

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # organization_id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("organizations.id"), index=True) # Assuming FK
    organization_id: Mapped[uuid.UUID] = mapped_column(SQLiteUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), name="createdAt", server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), name="updatedAt", default=func.now(), onupdate=func.now())

    # Relationship to users (many-to-many)
    users: Mapped[List["User"]] = relationship(
        secondary=user_roles_association, # Changed from "people_roles" string to the imported table object
        back_populates="roles"
    )

    # Relationship to permissions (many-to-many)
    permissions: Mapped[List["Permission"]] = relationship(
        secondary=role_permissions_association,
        back_populates="roles",
        lazy="selectin"  # Ensure selectin loading for permissions
    )

    # Optional: Add relationship to Organization if organization_id is a ForeignKey
    organization: Mapped["Organization"] = relationship(back_populates="roles")


    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"
