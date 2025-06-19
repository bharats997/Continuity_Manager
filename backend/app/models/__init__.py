# backend/app/models/__init__.py
# This file is intentionally left blank. Models should be imported directly
# from their respective modules (e.g., from app.models.domain.users import User)
# to avoid circular dependencies.

# Centralized metadata discovery for Alembic and SQLAlchemy is handled in
# app/db/base.py, which imports all necessary models.
from ..db.session import Base

__all__ = ['Base']
