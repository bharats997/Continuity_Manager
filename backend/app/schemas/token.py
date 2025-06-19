from typing import Optional, List
import uuid

from pydantic import BaseModel

# Properties to return to client on successful login
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Properties stored in the JWT token payload
class TokenPayload(BaseModel):
    sub: Optional[str] = None  # Subject (user identifier, typically email or user_id as string)
    user_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    scopes: List[str] = []
    # Standard claims like 'exp', 'iat', 'nbf' are usually handled by the JWT creation utility
    # and might not need to be explicitly defined here unless you have specific validation needs for them.
