import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator, Generator

from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, Session

from backend.app.main import app  # Import your FastAPI app
from backend.app.database.session import Base  # Import Base for creating tables
from backend.app.apis.deps import get_db  # Import get_db from where it's used by endpoints to override
from backend.app.models.domain import organizations, departments, people, roles, locations # Import all models to create tables
from backend.app.models.domain.organizations import Organization as OrganizationModel
from backend.app.models.domain.people import Person as PersonModel

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}, # check_same_thread is for SQLite
    poolclass=StaticPool # Ensures the same connection is used for in-memory DB
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """
    Create all tables in the in-memory SQLite database before tests run.
    Drop all tables after tests complete.
    `autouse=True` ensures this fixture is run automatically for the session.
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("DEBUG [conftest.py create_test_tables]: All tables created.")
        yield  # Allow tests to run
    except Exception as e:
        print(f"Error during table creation in create_test_tables: {e}")
        raise
    finally:
        Base.metadata.drop_all(bind=engine)
        print("DEBUG [conftest.py create_test_tables]: All tables dropped.")

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Provides a clean database session for each test function.
    Default data (org ID 1, user ID 1) is added as part of the test's transaction.
    The entire transaction is rolled back after the test to ensure isolation.
    """
    connection = engine.connect()
    # Each test gets a fresh transaction
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    default_org_created_in_fixture = False
    default_user_created_in_fixture = False

    try:
        # Setup: Add default data within this transaction if it doesn't exist
        # No session.commit() here for default data. It becomes part of the test's transaction.
        default_org = session.query(OrganizationModel).filter(OrganizationModel.id == 1).first()
        if not default_org:
            default_org = OrganizationModel(id=1, name="Default Test Organization", description="Org for placeholder user")
            session.add(default_org)
            default_org_created_in_fixture = True
            # print(f"DEBUG [conftest.py db_session]: Added default org (ID 1) to session.")
        
        default_user = session.query(PersonModel).filter(PersonModel.id == 1, PersonModel.organizationId == 1).first()
        if not default_user:
            # default_org (ID 1) should have been established by this point.
            # If session.get(OrganizationModel, 1) is None here, it means default_org wasn't properly added/fetched earlier.
            # We proceed assuming organizationId=1 is valid and refers to default_org.
            # No need to create a fallback org, as that causes the unique constraint error.
            pass # org_for_user is not strictly needed if we just use organizationId=1

            default_user = PersonModel(
                id=1, 
                email="default.user@example.com", 
                firstName="Default", 
                lastName="User",
                organizationId=1, 
                isActive=True
            )
            session.add(default_user)
            default_user_created_in_fixture = True
            # print(f"DEBUG [conftest.py db_session]: Added default user (ID 1, Org ID 1) to session.")
        
        # Flush to assign IDs to newly added default_org/default_user if they were created now
        # and to ensure they are in the identity map before expunging.
        if default_org_created_in_fixture or default_user_created_in_fixture:
            session.flush()
            # print(f"DEBUG [conftest.py db_session]: Flushed session to assign IDs to default data.")

        # Expunge them so API endpoints load them fresh from their own session, bound to API's session.
        # Ensure they exist and are in session before expunging.
        if default_user and default_user in session:
            session.expunge(default_user)
            # print(f"DEBUG [conftest.py db_session]: Expunged default_user from test session {id(session)}.")
        if default_org and default_org in session:
            session.expunge(default_org)
            # print(f"DEBUG [conftest.py db_session]: Expunged default_org from test session {id(session)}.")
        
        # print(f"DEBUG [conftest.py db_session]: Default data prepared, objects expunged. Yielding session {id(session)}.")
        yield session # Test runs now. Test can commit, but rollback in finally will undo.

    except Exception as e:
        print(f"Exception in db_session fixture or test: {e}")
        # Transaction will be rolled back in finally
        raise
    finally:
        # Teardown: Rollback the transaction after the test.
        # This ensures that any changes made by the test, AND the default data added at the start of this fixture,
        # are all rolled back, providing isolation.
        # print(f"DEBUG [conftest.py db_session]: Closing session {id(session)} in finally. Transaction active: {transaction.is_active if transaction else 'None'}")
        if session.is_active:
            session.close()
        
        if transaction and transaction.is_active:
            # print("DEBUG [conftest.py db_session]: Rolling back transaction.")
            transaction.rollback()
        
        if connection:
            # print("DEBUG [conftest.py db_session]: Closing connection.")
            if connection.in_transaction(): # Should not be the case if transaction.rollback() worked
                # print("DEBUG [conftest.py db_session]: Connection still in transaction, attempting connection rollback.")
                connection.rollback() # Try to clean up connection's transaction
            connection.close()

@pytest.fixture(scope="function")
def override_get_db(db_session: Session):
    """
    Overrides the `get_db` dependency in the FastAPI app to use the test database session.
    """
    def _override_get_db():
        try:
            yield db_session
        finally:
            db_session.close() # Ensure session is closed, though rollback handles data

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None) # Clean up override

@pytest.fixture(scope="session")
def event_loop():
    """
    Creates an event loop for the session.
    Required for pytest-asyncio with session-scoped async fixtures.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def test_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an AsyncClient for making requests to the FastAPI app.
    Depends on `override_get_db` to ensure the test DB is used.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
