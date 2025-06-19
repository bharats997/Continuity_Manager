# backend/app/schemas/user_audit.py
import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict

class UserAuditInfo(BaseModel):
    """Minimal user info for audit fields."""
    id: uuid.UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
