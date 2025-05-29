import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.orm import Session

# Assuming Pydantic models are in backend.app.models.department
# from backend.app.models.department import DepartmentCreate, DepartmentResponse
# Assuming SQLAlchemy Organization model is in backend.app.models.domain.organizations
from backend.app.models.domain.organizations import Organization as OrganizationModel

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

# Helper to create a dummy organization for tests
def create_test_organization(db_session: Session, name: str = "Test Org Inc.") -> OrganizationModel:
    org = OrganizationModel(name=name, description="A test organization")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org

async def test_create_department_success(test_client: AsyncClient, db_session: Session):
    test_org = create_test_organization(db_session, name="Org For Create Success Dept")
    
    department_data = {
        "name": "Human Resources",
        "description": "Handles all employee-related matters.",
        "organizationId": test_org.id
    }
    response = await test_client.post("/api/v1/departments/", json=department_data)
    
    assert response.status_code == status.HTTP_201_CREATED
    created_dept = response.json()
    assert created_dept["name"] == department_data["name"]
    assert created_dept["description"] == department_data["description"]
    assert created_dept["organizationId"] == department_data["organizationId"]
    assert "id" in created_dept
    assert created_dept["isActive"] is True # Default from SQLAlchemy model

async def test_create_department_duplicate_name_conflict(test_client: AsyncClient, db_session: Session):
    test_org = create_test_organization(db_session, name="Org For Duplicate Dept Test")

    department_data = {
        "name": "Finance Department",
        "description": "Initial finance department.",
        "organizationId": test_org.id
    }
    org_id = test_org.id # Store the ID before test_org can become detached

    # Create the first department
    response1 = await test_client.post("/api/v1/departments/", json=department_data)
    assert response1.status_code == status.HTTP_201_CREATED

    # Attempt to create another with the same name in the same org
    department_data_duplicate = {
        "name": "Finance Department", # Same name
        "description": "Duplicate finance department attempt.",
        "organizationId": org_id # Use stored ID
    }
    response2 = await test_client.post("/api/v1/departments/", json=department_data_duplicate)
    
    # Expecting a 409 Conflict based on department_service.py logic
    assert response2.status_code == status.HTTP_409_CONFLICT 
    error_detail = response2.json()
    assert "already exists" in error_detail["detail"]

async def test_list_departments_empty(test_client: AsyncClient, db_session: Session):
    # Ensure no departments exist for a new org, or filter by a non-existent org_id if needed
    # For simplicity, we'll just call it without creating any departments yet for the default test org
    # or create a new org and list its departments
    create_test_organization(db_session, name="Org For Empty List Test") # Create an org, but no depts in it

    # The current list_departments endpoint in departments.py doesn't filter by org_id from path/query
    # It relies on a simplified get_all_departments from the service.
    # For a true empty test, we'd need to ensure the DB is empty or filter.
    # Let's assume the test DB is clean per test due to fixtures.
    response = await test_client.get("/api/v1/departments/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [] # Expect an empty list

async def test_list_departments_with_data(test_client: AsyncClient, db_session: Session):
    # The API will query for departments in organizationId=1 due to get_current_user_placeholder
    # So, we create departments for organizationId=1.
    # No need to create a separate test_org for this specific test's API call.
    default_organization_id = 1
    
    dept1_data = {"name": "Marketing TestDept", "organizationId": default_organization_id}
    dept2_data = {"name": "Sales TestDept", "organizationId": default_organization_id}

    await test_client.post("/api/v1/departments/", json=dept1_data)
    await test_client.post("/api/v1/departments/", json=dept2_data)

    response = await test_client.get("/api/v1/departments/")
    assert response.status_code == status.HTTP_200_OK
    departments = response.json()
    assert len(departments) == 2
    
    dept_names = {dept["name"] for dept in departments}
    assert dept1_data["name"] in dept_names
    assert dept2_data["name"] in dept_names

# TODO: Add tests for GET by ID, PUT, DELETE, and RBAC if applicable at API level
