# backend/app/schemas/token_schemas.py
import uuid
from typing import Optional, List
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None  # Subject (user identifier, which is the user_id as a string)
    organization_id: Optional[str] = None # organization_id as a string
    scopes: List[str] = []  # List of permission strings
    exp: Optional[int] = None # Expiration time (Unix timestamp)
    iat: Optional[int] = None # Issued at time (Unix timestamp)
