# backend/app/database/session.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file, if it exists
# Useful for local development to keep credentials out of code
load_dotenv()

# --- Database Configuration ---
# It's highly recommended to use environment variables for sensitive data
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password") # Replace with your actual password or env var
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "bcms_db") # Replace with your actual database name or env var

# Asynchronous driver (aiomysql) can be used for async operations if needed
# For standard FastAPI, synchronous `mysqlclient` (or `pymysql`) is common.
# Ensure you have `mysqlclient` installed: pip install mysqlclient
# Or for pymysql: pip install pymysql
# DATABASE_URL = f"mysql+mysqlclient://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# --- SQLAlchemy Engine ---
# `pool_pre_ping` checks connections for liveness before use.
# `echo=True` can be useful for debugging SQL queries during development.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    # echo=True # Uncomment for debugging SQL
)

# --- SQLAlchemy Session ---
# SessionLocal will be used to create database sessions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Base for Declarative Models ---
# All SQLAlchemy ORM models will inherit from this Base.
Base = declarative_base()

# --- Dependency for FastAPI ---
def get_db():
    """
    FastAPI dependency to get a database session.
    Ensures the session is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

print(f"Database URL configured: mysql+pymysql://{DB_USER}:****@{DB_HOST}:{DB_PORT}/{DB_NAME}")
print("Ensure your MySQL server is running and the database exists.")
print("You might need to install pymysql: pip install pymysql")
