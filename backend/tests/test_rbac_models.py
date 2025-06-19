# backend/tests/test_rbac_models.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from typing import Generator
import uuid # Added for UUID generation

from app.db.base import Base
from app.models.domain.users import User
from app.models.domain.roles import Role
from app.models.domain.permissions import Permission
from app.models.domain.organizations import Organization
# from app.models import user_roles_table, role_permissions_table # Commented out, not used and likely incorrect names

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Define static UUIDs for test organizations in this file
TEST_ORG_ID_RBAC_PERSON_CREATE = uuid.UUID("10000000-0000-0000-0000-000000000001")
TEST_ORG_ID_RBAC_ROLE_ASSIGNEE = uuid.UUID("10000000-0000-0000-0000-000000000002")
TEST_ORG_ID_RBAC_PERMISSION_CHECK = uuid.UUID("10000000-0000-0000-0000-000000000003")

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session() -> Generator[SQLAlchemySession, None, None]:
    Base.metadata.create_all(bind=engine) # Create tables
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine) # Drop tables after test

# --- Test Cases ---

def test_create_user(db_session: SQLAlchemySession):
    # Ensure organization 1 exists
    org = Organization(id=TEST_ORG_ID_RBAC_PERSON_CREATE, name="Test Org")
    db_session.add(org)
    db_session.commit()

    user_data = {
        "firstName": "Test",
        "lastName": "User",
        "email": "test.user@example.com",
        # "hashed_password": "a_secure_hashed_password", # Removed: Not a field on Person SQLAlchemy model
        "organizationId": TEST_ORG_ID_RBAC_PERSON_CREATE,
        "jobTitle": "Tester"
    }
    new_user = User(**user_data)
    
    db_session.add(new_user)
    db_session.commit()
    db_session.refresh(new_user)
    
    retrieved_user = db_session.query(User).filter(User.id == new_user.id).first()
    
    assert retrieved_user is not None
    assert retrieved_user.email == user_data["email"]
    assert retrieved_user.firstName == user_data["firstName"]
    assert retrieved_user.lastName == user_data["lastName"]
    assert retrieved_user.organizationId == user_data["organizationId"]
    assert retrieved_user.isActive is True # Default value

def test_create_role(db_session: SQLAlchemySession):
    role_data = {
        "name": "Administrator",
        "description": "Manages the entire system"
    }
    new_role = Role(**role_data)
    
    db_session.add(new_role)
    db_session.commit()
    db_session.refresh(new_role)
    
    retrieved_role = db_session.query(Role).filter(Role.id == new_role.id).first()
    
    assert retrieved_role is not None
    assert retrieved_role.name == role_data["name"]
    assert retrieved_role.description == role_data["description"]

def test_create_permission(db_session: SQLAlchemySession):
    permission_data = {
        "name": "user:create",
        "description": "Allows creating new users"
    }
    new_permission = Permission(**permission_data)
    
    db_session.add(new_permission)
    db_session.commit()
    db_session.refresh(new_permission)
    
    retrieved_permission = db_session.query(Permission).filter(Permission.id == new_permission.id).first()
    
    assert retrieved_permission is not None
    assert retrieved_permission.name == permission_data["name"]
    assert retrieved_permission.description == permission_data["description"]

def test_assign_role_to_user(db_session: SQLAlchemySession):
    # Ensure organization 1 exists
    org = Organization(id=TEST_ORG_ID_RBAC_ROLE_ASSIGNEE, name="Test Org for Role Assignee")
    db_session.add(org)
    db_session.commit()

    # 1. Create a User
    user_data = {
        "firstName": "Role",
        "lastName": "Assignee",
        "email": "role.assignee@example.com",
        # "hashed_password": "password_hash", # Removed
        "organizationId": TEST_ORG_ID_RBAC_ROLE_ASSIGNEE 
    }
    test_user = User(**user_data)
    db_session.add(test_user)
    
    # 2. Create a Role
    role_data = {"name": "Editor", "description": "Can edit content"}
    test_role = Role(**role_data)
    db_session.add(test_role)
    
    db_session.commit() # Commit person and role first to get IDs
    db_session.refresh(test_role)

    # 3. Assign Role to User
    test_user.roles.append(test_role)
    db_session.commit()
    db_session.refresh(test_user) # Refresh to get the updated roles list
    
    # 4. Assertions
    assert test_role in test_user.roles
    
    # Optional: Check the other side of the relationship
    retrieved_role = db_session.query(Role).filter(Role.id == test_role.id).first()
    assert retrieved_role is not None
    assert test_user in retrieved_role.users

def test_assign_permission_to_role(db_session: SQLAlchemySession):
    # 1. Create a Role
    role_data = {"name": "ContentManager", "description": "Manages web content"}
    test_role = Role(**role_data)
    db_session.add(test_role)
    
    # 2. Create a Permission
    permission_data = {"name": "content:publish", "description": "Can publish content"}
    test_permission = Permission(**permission_data)
    db_session.add(test_permission)
    
    db_session.commit() # Commit role and permission first to get IDs
    db_session.refresh(test_role)
    db_session.refresh(test_permission)

    # 3. Assign Permission to Role
    test_role.permissions.append(test_permission)
    db_session.commit()
    db_session.refresh(test_role) # Refresh to get updated permissions list
    
    # 4. Assertions
    assert test_permission in test_role.permissions
    
    # Optional: Check the other side of the relationship
    retrieved_permission = db_session.query(Permission).filter(Permission.id == test_permission.id).first()
    assert retrieved_permission is not None
    assert test_role in retrieved_permission.roles

def test_user_has_permission_through_role(db_session: SQLAlchemySession):
    # Ensure organization 1 exists
    org = Organization(id=TEST_ORG_ID_RBAC_PERMISSION_CHECK, name="Test Org for Permission Check")
    db_session.add(org)
    db_session.commit()

    # 1. Create User
    user_data = {
        "firstName": "Permitted",
        "lastName": "User",
        "email": "permitted.user@example.com",
        # "hashed_password": "secure_hash", # Removed
        "organizationId": TEST_ORG_ID_RBAC_PERMISSION_CHECK
    }
    test_user = User(**user_data)
    db_session.add(test_user)

    # 2. Create Role
    role_data = {"name": "ArticlePublisher", "description": "Can publish articles"}
    test_role = Role(**role_data)
    db_session.add(test_role)

    # 3. Create Permission that will be assigned
    assigned_permission_data = {"name": "article:publish", "description": "Allows publishing articles"}
    test_assigned_permission = Permission(**assigned_permission_data)
    db_session.add(test_assigned_permission)
    
    # 3b. Create another Permission that will NOT be assigned
    unassigned_permission_data = {"name": "user:delete", "description": "Allows deleting users"}
    test_unassigned_permission = Permission(**unassigned_permission_data)
    db_session.add(test_unassigned_permission)

    # Commit initial entities to get IDs
    db_session.commit()
    db_session.refresh(test_user) # This should now correctly refer to the created user
    db_session.refresh(test_role)
    db_session.refresh(test_assigned_permission)
    db_session.refresh(test_unassigned_permission)


    # 4. Assign the specific Permission to the Role
    test_role.permissions.append(test_assigned_permission)
    
    # 5. Assign the Role to the Person
    test_user.roles.append(test_role)
    
    db_session.commit()
    
    # Retrieve the person again to ensure we're working with the latest session state
    # and relationships are loaded as they would be in application code.
    queried_user = db_session.query(User).filter(User.id == test_user.id).one()

    # 6. Check if person has the assigned permission
    has_assigned_permission = False
    for role_in_user in queried_user.roles:
        if test_assigned_permission in role_in_user.permissions:
            has_assigned_permission = True
            break
    assert has_assigned_permission is True

    # 7. Check that the person does NOT have the unassigned permission
    has_unassigned_permission = False
    for role_in_user in queried_user.roles:
        if test_unassigned_permission in role_in_user.permissions:
            has_unassigned_permission = True
            break
    assert has_unassigned_permission is False
