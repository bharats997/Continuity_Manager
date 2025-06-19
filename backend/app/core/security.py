# backend/app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, Union

from jose import jwt

from app.config import settings # Import settings from the new config.py


def get_password_hash(password: str) -> str:
    """Placeholder for password hashing logic."""
    # In a real application, use a strong hashing library like passlib
    # For example: from passlib.context import CryptContext
    # pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # return pwd_context.hash(password)
    return f"hashed_{password}" # Simple placeholder for now

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Placeholder for password verification logic."""
    # In a real application, use passlib's verify method
    # For example: return pwd_context.verify(plain_password, hashed_password)
    return hashed_password == f"hashed_{plain_password}" # Simple placeholder

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
