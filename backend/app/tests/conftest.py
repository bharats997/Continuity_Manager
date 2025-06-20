# app/tests/conftest.py

import pytest
import pytest_asyncio
import asyncio
import os
import sys
from pathlib import Path

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))) # Removed for running pytest from backend dir
# print(f"CONFTES_SYS_PATH_AFTER_INSERT: {sys.path}") # DEBUG_SYS_PATH

import logging
import sqlite3 # For type hinting dbapi_connection if needed
import uuid # For DEFAULT_ORG_ID
from typing import Any, AsyncGenerator, Callable, Union, Optional, List # For type hinting
import inspect # For signature inspection
from app.models.domain.users import User # Domain model
from app.config import settings # For PWD_CONTEXT and potentially other settings

# Default role name to be used in tests if not overridden
DEFAULT_USER_ROLE_NAME = "USER"

# Set database URLs for testing BEFORE any app modules are imported
# This ensures that app.db.session picks up the correct URL
# Define the absolute path for the test database file
# This ensures that all connections (from tests, from the app) point to the exact same file.
TEST_DB_FILENAME = "test_db.sqlite"
TEST_DB_PATH = Path(__file__).parent / TEST_DB_FILENAME

# Use the absolute path in the database URLs
ASYNC_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
SYNC_TEST_DB_URL = "sqlite:///:memory:"  # For any sync operations # For any sync operations

os.environ['ASYNC_DATABASE_URL'] = ASYNC_TEST_DB_URL
os.environ['DATABASE_URL'] = SYNC_TEST_DB_URL  # Set sync URL too if used by any part of app

# Ensure the FastAPI settings object sees these test URLs
from app.config import settings as app_settings
app_settings.ASYNC_TEST_DB_URL = ASYNC_TEST_DB_URL
app_settings.SYNC_TEST_DB_URL = SYNC_TEST_DB_URL
app_settings.TEST_DB_PATH = TEST_DB_PATH

# Import app-specific modules after setting environment variables
from fastapi import FastAPI
from sqlalchemy import text
from httpx import AsyncClient
from sqlalchemy import event, select, text # Restore event, select, text
from sqlalchemy.orm import sessionmaker # Keep sessionmaker
from sqlalchemy.pool import StaticPool # Keep one StaticPool, NullPool might be needed if used elsewhere, but was removed.
import logging # Keep logging
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from app.db.session import get_async_db
from app.db.base import Base # Import Base from a module that has all models imported
from app.db.session import AsyncSessionLocal as AppAsyncSessionLocal, get_async_engine_factory
from app.main import app as fastapi_app # Import the app instance from main
from sqlalchemy.ext.asyncio import async_sessionmaker # Import for test-specific session maker
from app.models.domain.organizations import Organization as OrganizationDB
from app.models.domain.bia_categories import BIACategory as BIACategoryDB # Corrected import for BIA Category fixture
from app.models.domain.users import User as UserDB
from app.models.domain.roles import Role as DomainRoleModel
from app.models.domain.permissions import Permission as PermissionDB
from app.schemas.role import RoleName as UserRole # For authenticated clients
from app.core.security import create_access_token # For authenticated clients
from app.config import settings # For JWT settings, DEFAULT_ORG_ID etc.

# --- Constants ---

# BIA Impact Criteria Permissions
BIA_IMPACT_CRITERIA_CREATE = "bia_impact_criteria:create"
BIA_IMPACT_CRITERIA_READ = "bia_impact_criteria:read"
BIA_IMPACT_CRITERIA_UPDATE = "bia_impact_criteria:update"
BIA_IMPACT_CRITERIA_DELETE = "bia_impact_criteria:delete"
BIA_IMPACT_CRITERIA_LIST = "bia_impact_criteria:list"

ALL_BIA_IMPACT_CRITERIA_PERMISSIONS = [
    BIA_IMPACT_CRITERIA_CREATE,
    BIA_IMPACT_CRITERIA_READ,
    BIA_IMPACT_CRITERIA_UPDATE,
    BIA_IMPACT_CRITERIA_DELETE,
    BIA_IMPACT_CRITERIA_LIST,
]

# BIA Category Permissions
BIA_CATEGORY_CREATE = "bia_category_create"
BIA_CATEGORY_READ = "bia_category_read"
BIA_CATEGORY_UPDATE = "bia_category_update"
BIA_CATEGORY_DELETE = "bia_category_delete"

ALL_BIA_CATEGORY_PERMISSIONS = [
    BIA_CATEGORY_CREATE,
    BIA_CATEGORY_READ,
    BIA_CATEGORY_UPDATE,
    BIA_CATEGORY_DELETE,
]

SQLITE_BUSY_TIMEOUT_MS = 15000  # milliseconds
logger = logging.getLogger(__name__)

# Define the log file path at the top, relative to this conftest.py file
LOG_FILE_PATH = Path(__file__).parent / "test_run.log"

# Use DEFAULT_ORG_ID from settings if available, otherwise define it
# Ensure this matches how your application expects/defines it.
DEFAULT_ORG_ID_STR = getattr(settings, 'DEFAULT_ORG_ID', "00000000-0000-0000-0000-000000000001")
DEFAULT_ORG_ID = uuid.UUID(DEFAULT_ORG_ID_STR)

_pragma_listener_globally_set = False # Module-level flag to ensure listener is set once

# --- Logging Configuration ---
@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """
    Hook to configure the test environment before any tests are run.
    """
    log_format = '%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)
    
    # Example: Add a FileHandler to also log to a file (optional)
    # log_file_path = "test_run.log" 
    # file_handler = logging.FileHandler(log_file_path, mode='w') # 'w' to overwrite each run
    # file_handler.setLevel(logging.DEBUG) # Or INFO, as needed
    # file_handler.setFormatter(logging.Formatter(log_format))
    # logging.getLogger().addHandler(file_handler) # Add to root logger
    
    logger.info("Pytest configuration complete. Logging initialized.")
    logger.info(f"ASYNC_DATABASE_URL set to: {os.environ.get('ASYNC_DATABASE_URL')}")
    logger.info(f"DATABASE_URL set to: {os.environ.get('DATABASE_URL')}")

# Session-scoped autouse fixture to set up file logging for the entire test session.
@pytest.fixture(scope="session", autouse=True)
def setup_file_logging():
    """Session-scoped autouse fixture to set up file logging for the entire test session."""
    # Ensure the log file is clean for each session (pytest run)
    if LOG_FILE_PATH.exists():
        LOG_FILE_PATH.unlink()

    # Create file handler
    file_handler = logging.FileHandler(LOG_FILE_PATH)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(name)-30s:%(lineno)4d - %(message)s')
    file_handler.setFormatter(formatter)

    # Add handler to the root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.DEBUG) # Ensure root logger processes DEBUG messages

    # Configure specific loggers (e.g., SQLAlchemy)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)
    
    # Log that file logging is set up
    # Use a generic logger here as specific app loggers might not be configured yet
    logging.info(f"File logging configured. All test session logs will be written to: {LOG_FILE_PATH.resolve()}")

    yield

    # Teardown: remove handler after tests are done for the session
    root_logger.removeHandler(file_handler)
    file_handler.close()

async def create_test_permission(db: AsyncSession, name: str, description: str) -> PermissionDB:
    """
    Creates a test permission if it doesn't already exist for the given organization.
    """
    # Check if permission already exists (permissions are global)
    stmt = select(PermissionDB).where(PermissionDB.name == name)
    result = await db.execute(stmt)
    existing_permission = result.scalars().first()

    if existing_permission:
        logger.info(f"Global permission '{name}' already exists. Skipping creation.")
        return existing_permission
    
    permission = PermissionDB(
        name=name,
        description=description
    )
    db.add(permission)
    # The session is managed by the calling fixture, which should handle commit/flush.
    logger.info(f"Created global permission '{name}'.")
    return permission

# --- Core Test Fixtures ---

@pytest_asyncio.fixture(scope="session")
async def async_db_session_for_session_scope(db_engine: AsyncEngine):
    """Yield an async database session for session-scoped fixtures."""
    TestAsyncSessionLocal = async_sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine, class_=AsyncSession
    )
    async with TestAsyncSessionLocal() as session:
        logger.info("Yielding session-scoped async DB session.")
        yield session
        logger.info("Closing session-scoped async DB session.")
    # No need to await session.close() here as context manager handles it

@pytest_asyncio.fixture(scope="session")
async def root_organization(async_db_session_for_session_scope: AsyncSession) -> OrganizationDB:
    """
    Provides the root/default organization object for session-scoped fixtures.
    Assumes the default organization has been created by the db_engine fixture.
    """
    logger.info("Fetching root organization for session-scoped fixtures.")
    # Ensure DEFAULT_ORG_ID is imported or accessible, e.g., from app.config.settings
    # Convert to string as DB stores UUIDs as CHAR(36)
    default_org_id_str = str(settings.DEFAULT_ORG_ID)
    stmt = select(OrganizationDB).where(OrganizationDB.id == default_org_id_str)
    result = await async_db_session_for_session_scope.execute(stmt)
    organization = result.scalars().one_or_none()
    if not organization:
        logger.warning(f"Root organization with ID {default_org_id_str} not found. Attempting to create it now.")
        try:
            organization = OrganizationDB(
                id=uuid.UUID(default_org_id_str),
                name="Default Test Organization",
                is_active=True # Explicitly set, though model might have a default
            )
            async_db_session_for_session_scope.add(organization)
            await async_db_session_for_session_scope.commit()
            await async_db_session_for_session_scope.refresh(organization)
            logger.info(f"Successfully created and committed root organization {organization.id} ({organization.name}).")
        except Exception as e:
            import traceback # Import locally for detailed error logging
            logger.error(f"Failed to create root organization during test setup: {e}\n{traceback.format_exc()}")
            raise # Re-raise the exception to fail the test setup clearly
    logger.info(f"Root organization {organization.id} ({organization.name}) is now available for the session.")
    return organization

@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_bia_impact_criteria_permissions_globally(async_db_session_for_session_scope: AsyncSession, root_organization: OrganizationDB):
    """Ensures all BIA Impact Criteria permissions are created once per session."""
    logger.info("Creating BIA Impact Criteria permissions globally for the test session.")
    for perm_name in ALL_BIA_IMPACT_CRITERIA_PERMISSIONS:
        await create_test_permission(
            db=async_db_session_for_session_scope,
            name=perm_name,
            description=f"Permission to {perm_name.split(':')[-1]} BIA Impact Criteria"
        )
    logger.info("Finished setting up the test database and tables.")

@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_bia_category_permissions_globally(async_db_session_for_session_scope: AsyncSession, root_organization: OrganizationDB):
    """Ensures all BIA Category permissions are created once per session."""
    logger.info("Creating BIA Category permissions globally for the test session.")
    for perm_name in ALL_BIA_CATEGORY_PERMISSIONS:
        await create_test_permission(
            db=async_db_session_for_session_scope,
            name=perm_name,
            description=f"Permission to {perm_name.replace('_', ' ').replace('bia category ', '')} BIA Categories"
        )
    logger.info("Finished creating BIA Category permissions globally.")

import asyncio
import pytest

# Session-scoped event_loop for pytest-asyncio.
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def db_engine(event_loop) -> AsyncGenerator[AsyncEngine, None]:
    logger.info(f"db_engine: START. Session-scoped database engine setup using explicit event_loop.")
    async_test_db_url = settings.ASYNC_TEST_DB_URL
    test_db_path = settings.TEST_DB_PATH
    sqlite_busy_timeout_ms = settings.SQLITE_BUSY_TIMEOUT_MS

    db_file_path = test_db_path.resolve()
    engine: Optional[AsyncEngine] = None

    try:
        if os.path.exists(db_file_path):
            logger.info(f"db_engine: Deleting existing test database: {db_file_path}")
            os.remove(db_file_path)
        else:
            logger.info(f"db_engine: Test database {db_file_path} not found, will be created.")

        engine = create_async_engine(
            async_test_db_url,
            echo=False, # Set to True for verbose SQL logging if needed
            poolclass=StaticPool,
            connect_args={"check_same_thread": False} # Required for SQLite with StaticPool
        )
        logger.info(f"db_engine: AsyncEngine created for URL: {async_test_db_url}")

        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragmas(dbapi_connection: sqlite3.Connection, connection_record):
            logger.info(f"set_sqlite_pragmas: Configuring PRAGMAs for new connection.")
            try:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA foreign_keys=ON;")
                cursor.execute(f"PRAGMA busy_timeout = {sqlite_busy_timeout_ms};")
                cursor.close()
                logger.info(f"set_sqlite_pragmas: PRAGMAs (WAL, foreign_keys, busy_timeout) set.")
            except Exception as e_pragma:
                logger.error(f"set_sqlite_pragmas: Error setting PRAGMAs: {e_pragma}", exc_info=True)
                raise

        logger.info("db_engine: SQLite PRAGMA event listener configured.")

        async with engine.begin() as conn:
            logger.info(f"db_engine: Creating all tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info(f"db_engine: All tables created successfully.")
        
        # NO DATA SEEDING - This is critical for test isolation.
        # Tests or function-scoped fixtures are responsible for their own specific data setup.

        logger.info(f"db_engine: Yielding engine. Tables created, no data seeded.")
        yield engine

    finally:
        if engine:
            logger.info(f"db_engine: Teardown - disposing engine and dropping tables.")
            try:
                async with engine.begin() as conn:
                    logger.info(f"db_engine: Dropping all tables...")
                    await conn.run_sync(Base.metadata.drop_all)
                logger.info(f"db_engine: All tables dropped successfully.")
            except Exception as e_drop:
                logger.error(f"db_engine: Error dropping tables during teardown: {e_drop}", exc_info=True)
            
            await engine.dispose()
            logger.info(f"db_engine: Engine disposed.")
        else:
            logger.info("db_engine: Teardown skipped, engine was not successfully created.")
        
        # Optional: Clean up the test DB file after tests if it's a file-based DB and not in-memory.
        # This is generally good practice for file-based test databases.
        # if async_test_db_url.startswith("sqlite+aiosqlite:///") and ":memory:" not in async_test_db_url:
        #     if os.path.exists(db_file_path):
        #         logger.info(f"db_engine: Deleting test database file {db_file_path} after session.")
        #         try:
        #             os.remove(db_file_path)
        #         except OSError as e_remove_file:
        #             logger.warning(f"db_engine: Could not remove test database file {db_file_path} post-session: {e_remove_file}")

    logger.info("db_engine: Session-scoped database engine setup complete. END")

@pytest_asyncio.fixture(scope="function")
async def async_db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Function-scoped fixture to provide a clean database session with a transaction
    for each test. Rolls back the transaction after the test, ensuring test isolation.
    This is the standard pattern for testing with SQLAlchemy.
    """
    connection = await db_engine.connect()
    trans = await connection.begin()

    TestAsyncSessionLocal = async_sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    session = TestAsyncSessionLocal()

    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()

# --- FastAPI Application and Client Fixtures ---

@pytest_asyncio.fixture(scope="function")
async def app(async_db_session: AsyncSession) -> AsyncGenerator[FastAPI, Any]:
    # This fixture is function-scoped, so the override is applied for each test.
    # It's crucial that the overridden dependency yields the *same session* as the test itself uses.
    # The original implementation might have created a new session, leading to transaction/state issues.
    async def override_get_async_db_for_test() -> AsyncGenerator[AsyncSession, None]:
        yield async_db_session

    fastapi_app.dependency_overrides[get_async_db] = override_get_async_db_for_test
    
    try:
        yield fastapi_app
    finally:
        fastapi_app.dependency_overrides.clear()

import pytest # Ensure pytest is imported if used in the class
import json # For formatting error output
from httpx import AsyncClient, Response, ASGITransport # Ensure Response is imported
from fastapi import FastAPI # Ensure FastAPI is imported
from typing import AsyncGenerator, Any # Ensure Any is imported

class DebuggingAsyncClientWrapper:
    """
    A wrapper for httpx.AsyncClient that provides better debugging information on
    HTTP errors (4xx/5xx responses), printing the response body to the console.
    """

    def __init__(self, client: "httpx.AsyncClient"):
        self._client = client

    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute access to the underlying httpx.AsyncClient.
        This allows the wrapper to be used as a drop-in replacement for the client,
        including accessing properties like `headers`.
        """
        return getattr(self._client, name)

    async def request(
        self, method: str, url: str, expect_error: bool = False, **kwargs
    ) -> "httpx.Response":
        """
        Makes a request and handles debugging for error responses.
        """
        # Make the actual request
        response = await self._client.request(method, url, **kwargs)

        # If we are not expecting an error and we get one, print debug info and fail
        if not expect_error and (response.is_client_error or response.is_server_error):
            try:
                error_data = response.json()
                # Pretty print the JSON error response
                print(f"\n--- UNEXPECTED HTTP ERROR ---\n")
                print(f"Request: {method} {url}")
                print(f"Status Code: {response.status_code}")
                print("Response JSON:")
                # Use json.dumps for indentation and sorting keys for readability
                print(json.dumps(error_data, indent=2, sort_keys=True))
                print(f"\n---------------------------\n")
            except json.JSONDecodeError:
                # If the response is not JSON, print the raw text
                print(f"\n--- UNEXPECTED HTTP ERROR (non-JSON response) ---\n")
                print(f"Request: {method} {url}")
                print(f"Status Code: {response.status_code}")
                print("Response Text:")
                print(response.text)
                print(f"\n-------------------------------------------------\n")
            
            # Use pytest.fail to stop the test immediately with a clear message
            pytest.fail(
                f"Unexpected {response.status_code} error for {method} {url}. See console for details."
            )

        return response

    async def get(self, url: str, **kwargs) -> "httpx.Response":
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> "httpx.Response":
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> "httpx.Response":
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> "httpx.Response":
        return await self.request("DELETE", url, **kwargs)
    
    async def patch(self, url: str, **kwargs: Any) -> "httpx.Response":
        return await self.request("PATCH", url, **kwargs)

    async def head(self, url: str, **kwargs: Any) -> "httpx.Response":
        return await self.request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs: Any) -> "httpx.Response":
        return await self.request("OPTIONS", url, **kwargs)

@pytest_asyncio.fixture(scope="function")
async def async_client(
    app: FastAPI,
) -> AsyncGenerator[DebuggingAsyncClientWrapper, None]:
    """
    Fixture to provide a debugging httpx.AsyncClient wrapper for making requests to the test app.
    This uses the ASGITransport to test the app directly without a running server.
    The wrapper automatically prints detailed error info for 422/500 responses.
    """
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    try:
        yield DebuggingAsyncClientWrapper(client)
    finally:
        await client.aclose()


# --- Authenticated Client Fixtures (Example) ---

@pytest_asyncio.fixture(scope="function")
async def async_client_authenticated_as_user_factory(
    async_client: "DebuggingAsyncClientWrapper", async_db_session: AsyncSession
) -> Callable:
    """
    Factory fixture to create an authenticated client for a given user.
    Creates the user if they don't exist.
    """
    async def _create_authenticated_client(
        user_identifier: Union[User, str],
        password: str = "testpassword",
        role_override: Optional[UserRole] = None,  # Use UserRole enum from schemas
        organization_id_override: Optional[uuid.UUID] = None,
        permissions_to_assign_to_role: Optional[List[str]] = None # Added for dynamic permission assignment to role
    ):
        logger = logging.getLogger(__name__)
        effective_email: str
        effective_role_name: str
        effective_organization_id: uuid.UUID

        if isinstance(user_identifier, User):
            effective_email = user_identifier.email
            effective_organization_id = organization_id_override if organization_id_override is not None else user_identifier.organization_id
            effective_role_name = role_override.value if role_override else DEFAULT_USER_ROLE_NAME
        elif isinstance(user_identifier, str):
            effective_email = user_identifier
            effective_role_name = role_override.value if role_override else DEFAULT_USER_ROLE_NAME
            effective_organization_id = organization_id_override if organization_id_override is not None else DEFAULT_ORG_ID
        else:
            raise TypeError(
                f"user_identifier must be a User domain model instance or an email string, got {type(user_identifier)}"
            )

        user_query = select(UserDB).options(selectinload(UserDB.roles).selectinload(DomainRoleModel.permissions)).filter_by(email=effective_email, organization_id=effective_organization_id)
        user_result = await async_db_session.execute(user_query)
        db_user = user_result.scalars().first()

        if not db_user:
            db_user = UserDB(
                id=uuid.uuid4(),
                first_name="Test",  # Default value, matches SQLAlchemy model attribute
                last_name="User",   # Default value, matches SQLAlchemy model attribute
                email=effective_email,
                password_hash=settings.PWD_CONTEXT.hash(password),
                is_active=True,
                organization_id=effective_organization_id
            )
            async_db_session.add(db_user)
            await async_db_session.flush()
            logger.info(f"Session {id(async_db_session)} flushed (if necessary) after ensuring user '{effective_email}' and role '{effective_role_name}'. Commit/rollback is managed by test fixture.")
            logger.info(
                f"Created test user '{effective_email}' in org '{effective_organization_id}'. Assigning role '{effective_role_name}'."
            )
        else:
            logger.info(
                f"Using existing test user '{db_user.email}' in org '{db_user.organization_id}'. Ensuring role '{effective_role_name}'."
            )
            await async_db_session.refresh(db_user, attribute_names=['roles'])
            if db_user.roles is None:
                db_user.roles = []

        role_stmt = (
            select(DomainRoleModel)
            .filter_by(name=effective_role_name, organization_id=effective_organization_id)
            .options(selectinload(DomainRoleModel.permissions))
        )
        role_result = await async_db_session.execute(role_stmt)
        db_domain_role = role_result.scalars().first()

        if not db_domain_role:
            logger.info(f"Role '{effective_role_name}' not found for org '{effective_organization_id}', creating it.")
            db_domain_role = DomainRoleModel(
                name=effective_role_name, 
                organization_id=effective_organization_id,
            )
            async_db_session.add(db_domain_role)
            await async_db_session.flush()
            await async_db_session.refresh(db_domain_role, attribute_names=['permissions']) # Ensure permissions are loaded

        # ---- START LOGIC for permissions_to_assign_to_role (runs for new or existing roles) ----
        if permissions_to_assign_to_role and db_domain_role: # db_domain_role must exist here
            if db_domain_role.permissions is None:
                db_domain_role.permissions = []
            
            existing_permission_names = {p.name for p in db_domain_role.permissions if p}
            permissions_added_to_role = False # Flag to check if we need to flush/refresh

            for perm_name_to_assign in permissions_to_assign_to_role:
                if perm_name_to_assign not in existing_permission_names:
                    perm_description = f"Auto-assigned test permission: {perm_name_to_assign}"
                    # create_test_permission is defined globally in conftest
                    permission_object = await create_test_permission(
                        db=async_db_session,
                        name=perm_name_to_assign,
                        description=perm_description
                    )
                    # create_test_permission adds to session if new.
                    db_domain_role.permissions.append(permission_object)
                    permissions_added_to_role = True
                    logger.info(f"Dynamically added permission '{perm_name_to_assign}' to role '{db_domain_role.name}' (org: {db_domain_role.organization_id}).")
            
            if permissions_added_to_role:
                await async_db_session.flush() # Flush changes to the role's permissions
                await async_db_session.refresh(db_domain_role, attribute_names=['permissions'])
        # ---- END LOGIC for permissions_to_assign_to_role ----

        # Ensure the user's roles are loaded. The user object was either just created
        # or fetched with roles preloaded. A refresh ensures we have the latest state.
        await async_db_session.refresh(db_user, attribute_names=['roles'])

        # Associate the user with the role if not already associated.
        # This relies on the role (and its permissions) being correctly seeded.
        if db_domain_role and not any(r.id == db_domain_role.id for r in db_user.roles):
            db_user.roles.append(db_domain_role)
            logger.info(f"Associated role '{effective_role_name}' with user '{effective_email}'.")
            # Flush to make the association available within the transaction.
            await async_db_session.flush()
            # Refresh the user again to ensure the roles collection is up-to-date for token creation.
            await async_db_session.refresh(db_user, attribute_names=['roles'])
        else:
            logger.info(f"User '{effective_email}' already has role '{effective_role_name}'.")

        # Eagerly load permissions for each role to prevent lazy-loading errors,
        # then collect all permissions for the token scopes.
        user_permissions = []
        for role in db_user.roles:
            if role:
                await async_db_session.refresh(role, attribute_names=['permissions'])
                if role.permissions:
                    for perm in role.permissions:
                        if perm and perm.name:
                            user_permissions.append(perm)
        logger.info(f"Permissions for user '{effective_email}' for token scopes: {[p.name for p in user_permissions]}")

        # Ensure all changes are persisted before token creation
        await async_db_session.flush()

        logger.info(f"_create_authenticated_client: Preparing token for user: id={db_user.id}, org_id={db_user.organization_id}, email='{db_user.email}', is_active={db_user.is_active}, roles={[r.name for r in db_user.roles if r]}")

        token_data = {
            "sub": str(db_user.id),  # Use user's UUID as the subject, converted to string
            "organization_id": str(db_user.organization_id),  # Convert org UUID to string
            "scopes": [p.name for p in user_permissions]
        }
        access_token = create_access_token(data=token_data)
        
        async_client.headers["Authorization"] = f"Bearer {access_token}"
        logger.info(f"Authenticated client configured for user '{effective_email}' with role '{effective_role_name}'.")
        return async_client, access_token, db_user # Return all three

    return _create_authenticated_client


@pytest_asyncio.fixture(scope="function")
async def ciso_user_authenticated_client(async_client_authenticated_as_user_factory):
    """Authenticated client for a CISO user."""
    return await async_client_authenticated_as_user_factory(
        user_identifier="ciso@example.com", 
        role_override=UserRole.CISO,
        organization_id_override=DEFAULT_ORG_ID
    )

@pytest_asyncio.fixture(scope="function")
async def admin_user_authenticated_client(async_client_authenticated_as_user_factory):
    """Authenticated client for an ADMIN user."""
    return await async_client_authenticated_as_user_factory(
        user_identifier="admin@example.com", 
        role_override=UserRole.ADMIN,
        organization_id_override=DEFAULT_ORG_ID
    )

@pytest_asyncio.fixture(scope="function")
async def bcm_manager_user_authenticated_client(async_client_authenticated_as_user_factory):
    """Authenticated client for a BCM_MANAGER user."""
    return await async_client_authenticated_as_user_factory(
        user_identifier="bcm_manager@example.com", 
        role_override=UserRole.BCM_MANAGER,
        organization_id_override=DEFAULT_ORG_ID
    )

@pytest_asyncio.fixture(scope="function")
async def internal_auditor_user_authenticated_client(async_client_authenticated_as_user_factory):
    """Authenticated client for an INTERNAL_AUDITOR user."""
    return await async_client_authenticated_as_user_factory(
        user_identifier="internal_auditor@example.com", 
        role_override=UserRole.INTERNAL_AUDITOR,
        organization_id_override=DEFAULT_ORG_ID
    )

@pytest_asyncio.fixture(scope="function")
async def general_user_authenticated_client(async_client_authenticated_as_user_factory):
    """Authenticated client for a general USER role."""
    return await async_client_authenticated_as_user_factory(
        user_identifier="general_user@example.com", 
        role_override=UserRole.USER,
        organization_id_override=DEFAULT_ORG_ID
    )

@pytest_asyncio.fixture(scope="function")
async def async_default_app_user(
    async_db_session: AsyncSession, 
    ciso_user_authenticated_client: "AsyncClient" # Ensure CISO user is created by factory
) -> UserDB:
    """Fixture to get the default CISO user object from the database.
    
    This user (ciso@example.com) is the one for whom ciso_user_authenticated_client
    is set up.
    """
    # The ciso_user_authenticated_client fixture ensures the user and role exist.
    # We just need to fetch the user object.
    user_email = "ciso@example.com"
    organization_id = DEFAULT_ORG_ID

    stmt = select(UserDB).options(
        selectinload(UserDB.organization),
        selectinload(UserDB.roles).selectinload(DomainRoleModel.permissions)
    ).where(
        UserDB.email == user_email,
        UserDB.organization_id == organization_id
    )
    result = await async_db_session.execute(stmt)
    user = result.scalars().first()

    if not user:
        # This should ideally not happen if ciso_user_authenticated_client ran successfully
        # as it's supposed to create this user.
        raise ValueError(
            f"Default CISO user {user_email} in org {organization_id} not found in DB. "
            f"Ensure ciso_user_authenticated_client fixture ran and created the user."
        )
    
    logger.info(f"Retrieved async_default_app_user: {user.email} (ID: {user.id}) from org {user.organization_id}")
    return user


@pytest_asyncio.fixture(scope="function")
async def bcm_manager_user_async(
    async_db_session: AsyncSession, 
    bcm_manager_user_authenticated_client: "AsyncClient"
) -> UserDB:
    """Fixture to get the BCM Manager user object from the database."""
    user_email = "bcm_manager@example.com"
    stmt = select(UserDB).options(
        selectinload(UserDB.organization),
        selectinload(UserDB.roles).selectinload(DomainRoleModel.permissions)
    ).where(UserDB.email == user_email, UserDB.organization_id == DEFAULT_ORG_ID)
    user = (await async_db_session.execute(stmt)).scalars().first()
    if not user:
        raise ValueError(f"BCM Manager user {user_email} not found.")
    return user

@pytest_asyncio.fixture(scope="function")
async def internal_auditor_user_async(
    async_db_session: AsyncSession, 
    internal_auditor_user_authenticated_client: "AsyncClient"
) -> UserDB:
    """Fixture to get the Internal Auditor user object from the database."""
    user_email = "internal_auditor@example.com"
    stmt = select(UserDB).options(
        selectinload(UserDB.organization),
        selectinload(UserDB.roles).selectinload(DomainRoleModel.permissions)
    ).where(UserDB.email == user_email, UserDB.organization_id == DEFAULT_ORG_ID)
    user = (await async_db_session.execute(stmt)).scalars().first()
    if not user:
        raise ValueError(f"Internal Auditor user {user_email} not found.")
    return user

@pytest_asyncio.fixture(scope="function")
async def general_user_async(
    async_db_session: AsyncSession, 
    general_user_authenticated_client: "AsyncClient"
) -> UserDB:
    """Fixture to get the General User object from the database."""
    user_email = "general_user@example.com"
    stmt = select(UserDB).options(
        selectinload(UserDB.organization),
        selectinload(UserDB.roles).selectinload(DomainRoleModel.permissions)
    ).where(UserDB.email == user_email, UserDB.organization_id == DEFAULT_ORG_ID)
    user = (await async_db_session.execute(stmt)).scalars().first()
    if not user:
        raise ValueError(f"General user {user_email} not found.")
    return user

@pytest_asyncio.fixture(scope="function")
async def test_bia_category(
    async_db_session: AsyncSession, 
    root_organization: OrganizationDB, 
    bcm_manager_user_async: UserDB # Assuming BCM manager creates this
) -> BIACategoryDB:
    """Creates a sample BIA Category for testing."""
    from app.models.domain.bia_categories import BIACategory as BIACategoryDB # Import here to avoid circularity if any
    from uuid import uuid4

    category_name = f"Test BIA Category {uuid4()}"
    bia_category = BIACategoryDB(
        name=category_name,
        description="A test BIA category for impact criteria.",
        organization_id=root_organization.id,
        created_by_id=bcm_manager_user_async.id,
        updated_by_id=bcm_manager_user_async.id,
    )
    async_db_session.add(bia_category)
    await async_db_session.commit()
    await async_db_session.refresh(bia_category)
    logger.info(f"Created test_bia_category: {bia_category.name} (ID: {bia_category.id}) in org {bia_category.organization_id}")
    return bia_category


# --- BIA Impact Criteria Test Users & Clients ---

@pytest_asyncio.fixture(scope="function")
async def bcm_manager_bia_setup(
    async_client_authenticated_as_user_factory,
    create_bia_impact_criteria_permissions_globally # Ensure permissions are created
):
    """
    Sets up a BCM Manager equivalent user with all BIA Impact Criteria permissions.
    Uses a unique email to avoid conflict with the generic bcm_manager@example.com.
    Returns a tuple (client, token, user_object).
    """
    return await async_client_authenticated_as_user_factory(
        user_identifier="bcm_manager_for_bia@example.com", 
        role_override=UserRole.BCM_MANAGER, # Or a custom role if BCM_MANAGER shouldn't have these by default
        organization_id_override=DEFAULT_ORG_ID,
        permissions_to_assign_to_role=ALL_BIA_IMPACT_CRITERIA_PERMISSIONS
    )

@pytest_asyncio.fixture(scope="function")
async def user_with_bia_create_permissions_client(bcm_manager_bia_setup):
    """Provides an authenticated client for a user with BIA create permissions."""
    return bcm_manager_bia_setup[0]

@pytest_asyncio.fixture(scope="function")
async def access_token_for_user_with_bia_create_permissions(bcm_manager_bia_setup):
    """Provides an access token for a user with BIA create permissions."""
    return bcm_manager_bia_setup[1]

@pytest_asyncio.fixture(scope="function")
async def test_user_with_bia_create_permission(bcm_manager_bia_setup) -> UserDB:
    """Provides a UserDB object for a user with BIA create permissions."""
    return bcm_manager_bia_setup[2]

# Aliases for other permissions, since bcm_manager_bia_setup has all of them
@pytest_asyncio.fixture(scope="function")
async def access_token_for_user_with_bia_read_permission(bcm_manager_bia_setup):
    return bcm_manager_bia_setup[1]

@pytest_asyncio.fixture(scope="function")
async def access_token_for_user_with_bia_list_permission(bcm_manager_bia_setup):
    return bcm_manager_bia_setup[1]

@pytest_asyncio.fixture(scope="function")
async def access_token_for_user_with_bia_update_permission(bcm_manager_bia_setup):
    return bcm_manager_bia_setup[1]

@pytest_asyncio.fixture(scope="function")
async def access_token_for_user_with_bia_delete_permission(bcm_manager_bia_setup):
    return bcm_manager_bia_setup[1]


@pytest_asyncio.fixture(scope="function")
async def standard_user_bia_setup(
    async_client_authenticated_as_user_factory,
    create_bia_impact_criteria_permissions_globally # Permissions should exist, just not assigned to this user's role
):
    """
    Sets up a Standard User equivalent WITHOUT BIA Impact Criteria permissions.
    Uses a unique email.
    Returns a tuple (client, token, user_object).
    """
    return await async_client_authenticated_as_user_factory(
        user_identifier="standard_user_for_bia@example.com",
        role_override=UserRole.USER, # Assuming UserRole.USER is a basic role without these perms
        organization_id_override=DEFAULT_ORG_ID,
        permissions_to_assign_to_role=[] # Explicitly no BIA perms for this role instance
    )

@pytest_asyncio.fixture(scope="function")
async def user_without_bia_create_permissions_client(standard_user_bia_setup):
    """Provides an authenticated client for a user without BIA create permissions."""
    return standard_user_bia_setup[0]

@pytest_asyncio.fixture(scope="function")
async def access_token_for_user_without_bia_create_permissions(standard_user_bia_setup):
    """Provides an access token for a user without BIA create permissions."""
    return standard_user_bia_setup[1]

@pytest_asyncio.fixture(scope="function")
async def test_user_without_bia_create_permission(standard_user_bia_setup) -> UserDB:
    """Provides a UserDB object for a user without BIA create permissions."""
    return standard_user_bia_setup[2]


# --- BIA Category Test Users & Clients ---

@pytest_asyncio.fixture(scope="function")
async def bcm_manager_bia_category_setup(
    async_client_authenticated_as_user_factory,
    create_bia_category_permissions_globally # Ensure permissions are created
):
    """
    Sets up a BCM Manager user with all BIA Category permissions.
    Uses a unique email.
    Returns a tuple (client, token, user_object).
    """
    return await async_client_authenticated_as_user_factory(
        user_identifier="bcm_manager_for_bia_category@example.com", 
        role_override=UserRole.BCM_MANAGER,
        organization_id_override=DEFAULT_ORG_ID,
        permissions_to_assign_to_role=ALL_BIA_CATEGORY_PERMISSIONS
    )

@pytest_asyncio.fixture(scope="function")
async def bcm_manager_bia_category_client(bcm_manager_bia_category_setup):
    """Provides an authenticated client for a BCM Manager with BIA Category permissions."""
    return bcm_manager_bia_category_setup[0]

@pytest_asyncio.fixture(scope="function")
async def bcm_manager_bia_category_token(bcm_manager_bia_category_setup):
    """Provides an access token for a BCM Manager with BIA Category permissions."""
    return bcm_manager_bia_category_setup[1]

@pytest_asyncio.fixture(scope="function")
async def bcm_manager_bia_category_user(bcm_manager_bia_category_setup) -> UserDB:
    """Provides a UserDB object for a BCM Manager with BIA Category permissions."""
    return bcm_manager_bia_category_setup[2]

@pytest_asyncio.fixture(scope="function")
async def ciso_bia_category_setup(
    async_client_authenticated_as_user_factory,
    create_bia_category_permissions_globally # Ensure permissions are created
):
    """
    Sets up a CISO user with all BIA Category permissions.
    Uses a unique email.
    Returns a tuple (client, token, user_object).
    """
    return await async_client_authenticated_as_user_factory(
        user_identifier="ciso_for_bia_category@example.com", 
        role_override=UserRole.CISO,
        organization_id_override=DEFAULT_ORG_ID,
        permissions_to_assign_to_role=ALL_BIA_CATEGORY_PERMISSIONS
    )

@pytest_asyncio.fixture(scope="function")
async def ciso_bia_category_client(ciso_bia_category_setup):
    """Provides an authenticated client for a CISO with BIA Category permissions."""
    return ciso_bia_category_setup[0]

@pytest_asyncio.fixture(scope="function")
async def ciso_bia_category_token(ciso_bia_category_setup):
    """Provides an access token for a CISO with BIA Category permissions."""
    return ciso_bia_category_setup[1]

@pytest_asyncio.fixture(scope="function")
async def ciso_bia_category_user(ciso_bia_category_setup) -> UserDB:
    """Provides a UserDB object for a CISO with BIA Category permissions."""
    return ciso_bia_category_setup[2]

@pytest_asyncio.fixture(scope="function")
async def read_only_bia_category_user_setup(
    async_client_authenticated_as_user_factory,
    create_bia_category_permissions_globally
):
    """
    Sets up a standard USER with only BIA Category read permissions.
    Uses a unique email.
    Returns a tuple (client, token, user_object).
    """
    return await async_client_authenticated_as_user_factory(
        user_identifier="readonly_user_for_bia_category@example.com", 
        role_override=UserRole.USER, # Standard user
        organization_id_override=DEFAULT_ORG_ID,
        permissions_to_assign_to_role=[BIA_CATEGORY_READ]
    )

@pytest_asyncio.fixture(scope="function")
async def read_only_bia_category_client(read_only_bia_category_user_setup):
    """Provides an authenticated client for a user with read-only BIA Category permissions."""
    return read_only_bia_category_user_setup[0]

@pytest_asyncio.fixture(scope="function")
async def read_only_bia_category_token(read_only_bia_category_user_setup):
    """Provides an access token for a user with read-only BIA Category permissions."""
    return read_only_bia_category_user_setup[1]

@pytest_asyncio.fixture(scope="function")
async def read_only_bia_category_user(read_only_bia_category_user_setup) -> UserDB:
    """Provides a UserDB object for a user with read-only BIA Category permissions."""
    return read_only_bia_category_user_setup[2]

@pytest_asyncio.fixture(scope="function")
async def no_bia_category_permissions_user_setup(
    async_client_authenticated_as_user_factory,
    create_bia_category_permissions_globally
):
    """
    Sets up a standard USER with NO BIA Category permissions.
    Uses a unique email.
    Returns a tuple (client, token, user_object).
    """
    return await async_client_authenticated_as_user_factory(
        user_identifier="noperms_user_for_bia_category@example.com", 
        role_override=UserRole.USER, # Standard user
        organization_id_override=DEFAULT_ORG_ID,
        permissions_to_assign_to_role=[] # Explicitly no BIA Category permissions
    )

@pytest_asyncio.fixture(scope="function")
async def no_bia_category_permissions_client(no_bia_category_permissions_user_setup):
    """Provides an authenticated client for a user with no BIA Category permissions."""
    return no_bia_category_permissions_user_setup[0]

@pytest_asyncio.fixture(scope="function")
async def no_bia_category_permissions_token(no_bia_category_permissions_user_setup):
    """Provides an access token for a user with no BIA Category permissions."""
    return no_bia_category_permissions_user_setup[1]

@pytest_asyncio.fixture(scope="function")
async def no_bia_category_permissions_user(no_bia_category_permissions_user_setup) -> UserDB:
    """Provides a UserDB object for a user with no BIA Category permissions."""
    return no_bia_category_permissions_user_setup[2]



