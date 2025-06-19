# backend/app/config.py
import os
from pathlib import Path
from passlib.context import CryptContext

class Settings:
    PROJECT_NAME: str = "Continuity Manager by CyRAACS"
    PROJECT_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_changed") # Change this!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Password Hashing
    PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Default Organization ID (as string, consistent with conftest.py usage)
    DEFAULT_ORG_ID: str = "00000000-0000-0000-0000-000000000001"

    # Database Settings
    # ASYNC_TEST_DB_URL is used by the test suite's db_engine fixture
    ASYNC_TEST_DB_URL: str = os.getenv("ASYNC_TEST_DB_URL", "sqlite+aiosqlite:///./test_db.sqlite")
    # DATABASE_URL is often used for synchronous operations or Alembic
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test_db.sqlite")

    # Test Database Specific Path - ensure this corresponds to ASYNC_TEST_DB_URL if file-based.
    # The conftest.py db_engine fixture expects settings.TEST_DB_PATH to be a Path object.
    _test_db_path_str = os.getenv("TEST_DB_PATH", "./test_db.sqlite") # Default path string
    TEST_DB_PATH: Path = Path(_test_db_path_str)

    # SQLite specific timeout for busy connections, used in test PRAGMAs
    SQLITE_BUSY_TIMEOUT_MS: int = int(os.getenv("SQLITE_BUSY_TIMEOUT_MS", "5000"))

settings = Settings()
