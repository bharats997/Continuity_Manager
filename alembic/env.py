import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

from dotenv import load_dotenv

# Add project root to sys.path to allow for absolute imports from backend
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
from backend.app.db.session import Base  # Corrected import for Base
# Ensure all models are imported here so Base.metadata is populated
# All models are imported directly below to register them with the Base imported above.
from backend.app.models.domain.users import User, user_roles_association  # noqa: F401
from backend.app.models.domain.roles import Role  # noqa: F401
from backend.app.models.domain.permissions import Permission, role_permissions_association  # noqa: F401
from backend.app.models.domain.organizations import Organization  # noqa: F401
from backend.app.models.domain.bia_categories import BIACategory  # noqa: F401
from backend.app.models.domain.applications import Application  # noqa: F401
from backend.app.models.domain.departments import Department, department_locations_association  # noqa: F401
from backend.app.models.domain.locations import Location  # noqa: F401
from backend.app.models.domain.processes import Process, process_locations_association, process_applications_association, process_dependencies_association  # noqa: F401
from backend.app.models.domain.vendors import Vendor  # noqa: F401
from backend.app.models.domain.bia_impact_scales import BIAImpactScale  # noqa: F401
from backend.app.models.domain.bia_impact_scale_levels import BIAImpactScaleLevel  # noqa: F401
from backend.app.models.domain.bia_timeframes import BIATimeframe  # noqa: F401
from backend.app.models.domain.bia_impact_criteria import BIAImpactCriterion, BIAImpactCriterionLevel  # noqa: F401

# Explicitly configure mappers after all models are imported if needed, though usually not required here
# as models register themselves upon import when inheriting from Base.
# Base.registry.configure() # This was in db/base.py, might be useful if auto-detection fails.

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Load .env file from the project root
# Ensure .env is in PROJECT_ROOT or adjust path accordingly
# For example, if .env is in the same directory as alembic.ini (project root)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'), override=True)

# Construct DATABASE_URL from environment variables
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password") # User should verify this default if needed
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "bcms_db")
# Ensure you have pymysql installed: pip install pymysql (already satisfied as per previous logs)
DB_SOCKET = os.getenv("DB_SOCKET")

if DB_SOCKET:
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?unix_socket={DB_SOCKET}"
else:
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=DATABASE_URL,  # Use the constructed DATABASE_URL
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
