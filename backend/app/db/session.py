import os
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

# Base for all models
Base = declarative_base()

# --- Engine Configuration ---

def get_async_engine_factory() -> AsyncEngine:
    """
    Factory function to create a new SQLAlchemy async engine.
    The database URL is retrieved from an environment variable.
    This function should be used by tests or any part of the system
    that requires a distinct engine instance.
    """
    database_url = os.getenv("ASYNC_DATABASE_URL", "sqlite+aiosqlite:///./default_async.db")
    # For test environments, ASYNC_DATABASE_URL is typically overridden to :memory:
    
    engine_args = {
        "echo": True,  # Set to True for SQL query logging, make False or configurable for production
        "poolclass": NullPool,  # Using NullPool ensures fresh connections, good for tests and can simplify async greenlet issues
    }
    # Note: connect_args for 'check_same_thread' is for the standard sync sqlite3 driver, not needed for aiosqlite.
    return create_async_engine(database_url, **engine_args)

_main_app_engine_instance: Optional[AsyncEngine] = None

def get_main_app_engine() -> AsyncEngine:
    """
    Returns the singleton SQLAlchemy async engine for the main application.
    Initializes it on the first call using the engine factory.
    This engine is intended for use by the running application (not tests).
    """
    global _main_app_engine_instance
    if _main_app_engine_instance is None:
        _main_app_engine_instance = get_async_engine_factory()
    return _main_app_engine_instance

# --- Session Configuration ---

# This is the primary session factory. It remains unbound here.
# For the application: it's bound to the main app engine within get_async_db.
# For tests: a separate test-specific session maker is created in conftest.py,
# bound to a test-specific engine.
AsyncSessionLocal = async_sessionmaker(
    class_=AsyncSession,
    expire_on_commit=False,  # Recommended for FastAPI to prevent issues with background tasks
    autocommit=False,
    autoflush=False,
)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a SQLAlchemy async session for the application.
    It uses the main application's singleton engine instance.
    """
    app_engine = get_main_app_engine() # Get the application's dedicated engine
    
    # Create a session from AsyncSessionLocal, binding the app's engine for this specific session.
    # This does not modify AsyncSessionLocal globally.
    async with AsyncSessionLocal(bind=app_engine) as session:
        try:
            yield session
            # Commits are typically handled by the service layer or specific CRUD operations,
            # not automatically in the dependency.
        except Exception:
            # Rollback in case of any exception to ensure data integrity
            await session.rollback()
            raise
        # No finally block needed for session.close() as async with handles it.
