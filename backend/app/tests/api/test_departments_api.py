import uuid
from typing import List, Optional

import pytest
import pytest_asyncio
from fastapi import Depends, HTTPException, status
from httpx import AsyncClient
from sqlalchemy.orm import Session, joinedload

# Main app and dependencies
from app.main import app
from app.apis import deps # For app.dependency_overrides[deps.get_current_user_placeholder]
from app.apis.deps import DepartmentPermissions

# Pydantic Models (API facing)
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)

# SQLAlchemy Models (Domain)
from app.models.domain.departments import Department as DepartmentModel
from app.models.domain.locations import Location as LocationModel
from app.models.domain.organizations import Organization as OrganizationModel
from app.models.domain.users import User as PersonModel
from app.models.domain.permissions import Permission as PermissionModel
from app.models.domain.roles import Role as RoleModel

# Test specific helpers and constants
from app.tests.helpers import DEFAULT_ORG_ID, DEFAULT_USER_ID

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

# Helper to create a dummy organization for tests
def create_test_organization(db_session: Session, name: str = "Test Org Inc.", org_id: uuid.UUID = DEFAULT_ORG_ID) -> OrganizationModel:
    # Check if org with this ID already exists to prevent PK violation if called multiple times with default
    org = db_session.query(OrganizationModel).filter(OrganizationModel.id == org_id).first()
    if org:
        return org
    org = OrganizationModel(id=org_id, name=name, description="A test organization")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org

# Helper to create a dummy role
def create_test_role(db_session: Session, name: str, organization_id: uuid.UUID, permission_names: List[str] = None, description: Optional[str] = None) -> RoleModel:
    # First, ensure all permissions exist or create them
    permissions = []
    if permission_names:
        for perm_name in permission_names:
            permission = db_session.query(PermissionModel).filter(PermissionModel.name == perm_name).first()
            if not permission:
                permission = PermissionModel(name=perm_name, description=f"Permission for {perm_name}")
                db_session.add(permission)
            permissions.append(permission)
    
    role = RoleModel(
        name=name,
        description=description,
        organization_id=organization_id,
        permissions=permissions
        # createdBy=DEFAULT_USER_ID # createdBy is not a direct field on RoleModel
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role

# Helper to create a dummy person
def create_test_person(
    db_session: Session, 
    first_name: str = "Test", 
    last_name: str = "User", 
    email_prefix: str = "test.user", 
    organization_id: uuid.UUID = DEFAULT_ORG_ID,
    roles: Optional[List[RoleModel]] = None
) -> PersonModel:
    person = PersonModel(
        firstName=first_name,
        lastName=last_name,
        email=f"{email_prefix}.{db_session.query(PersonModel).filter(PersonModel.email.like(f'{email_prefix}%@example.com')).count() + 1}@example.com", # Ensure unique email for the prefix
        organizationId=organization_id,
        createdBy=DEFAULT_USER_ID, # Assuming createdBy and updatedBy are UUIDs
        updatedBy=DEFAULT_USER_ID,
        isActive=True
    )
    if roles:
        person.roles.extend(roles)
    
    db_session.add(person)
    db_session.commit()
    db_session.refresh(person)
    # Eager load roles to verify they are set, useful for debugging tests
    db_session.refresh(person, attribute_names=['roles'])
    return person

# Helper to create a dummy location
def create_test_location(db_session: Session, name: str = "Test Location", organization_id: uuid.UUID = DEFAULT_ORG_ID, city: str = "Test City", country: str = "Testland") -> LocationModel:
    location = LocationModel(
        name=name,
        organizationId=organization_id,
        address_line1="123 Test St",
        city=city,
        country=country
    )
    db_session.add(location)
    db_session.commit()
    db_session.refresh(location)
    return location

# Helper to create a dummy department
def create_test_department(
    db_session: Session, 
    name: str = "Test Department", 
    organization_id: uuid.UUID = DEFAULT_ORG_ID, 
    description: Optional[str] = "Default test department description."
) -> DepartmentModel:
    department = DepartmentModel(
        name=name,
        organizationId=organization_id,
        description=description,
        createdBy=DEFAULT_USER_ID, # Assuming audit fields are desirable for test data
        updatedBy=DEFAULT_USER_ID
    )
    db_session.add(department)
    db_session.commit()
    db_session.refresh(department)
    return department

async def test_create_department_success(authenticated_test_client: AsyncClient, db_session: Session):
    
    department_data = {
        "name": "Human Resources",
        "description": "Handles all employee-related matters.",
        "organizationId": str(DEFAULT_ORG_ID) # Use string UUID in payload
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    
    assert response.status_code == status.HTTP_201_CREATED
    created_dept = response.json()
    assert created_dept["name"] == department_data["name"]
    assert created_dept["description"] == department_data["description"]
    assert created_dept["organizationId"] == department_data["organizationId"]
    assert "id" in created_dept
    assert created_dept["isActive"] is True # Default from SQLAlchemy model
    # Audit fields createdBy and updatedBy are not in the response schema.

async def test_create_department_empty_name(authenticated_test_client: AsyncClient, db_session: Session):
    department_data = {
        "name": "",  # Empty name
        "description": "Test department with empty name.",
        "organizationId": str(DEFAULT_ORG_ID)
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_department_name_too_long(authenticated_test_client: AsyncClient, db_session: Session):
    long_name = "a" * 256  # Exceeds max_length of 255
    department_data = {
        "name": long_name,
        "description": "Test department with excessively long name.",
        "organizationId": str(DEFAULT_ORG_ID)
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_department_description_too_long(authenticated_test_client: AsyncClient, db_session: Session):
    long_description = "d" * 1001  # Exceeds max_length of 1000
    department_data = {
        "name": "Valid Name",
        "description": long_description,
        "organizationId": str(DEFAULT_ORG_ID)
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_department_malformed_organization_id(authenticated_test_client: AsyncClient, db_session: Session):
    department_data = {
        "name": "OrgID Test Dept",
        "description": "Testing with a malformed organization ID.",
        "organizationId": "not-a-valid-uuid"
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_department_malformed_dept_head_id(authenticated_test_client: AsyncClient, db_session: Session):
    department_data = {
        "name": "Dept Head Test Dept",
        "description": "Testing with a malformed department head ID.",
        "organizationId": str(DEFAULT_ORG_ID),
        "department_head_id": "not-a-valid-uuid-for-head"
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_department_non_existent_dept_head_id(authenticated_test_client: AsyncClient, db_session: Session):
    non_existent_uuid = str(uuid.uuid4())
    department_data = {
        "name": "Dept Head Non-Existent Test",
        "description": "Testing with a non-existent department head ID.",
        "organizationId": str(DEFAULT_ORG_ID),
        "department_head_id": non_existent_uuid
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_department_dept_head_id_different_org(authenticated_test_client: AsyncClient, db_session: Session):
    # Create a second organization
    other_org_id = uuid.uuid4()
    create_test_organization(db_session, name="Other Test Org Inc.", org_id=other_org_id)

    # Create a person in this 'other' organization
    person_in_other_org = create_test_person(db_session, email_prefix="other.org.user", organization_id=other_org_id)

    department_data = {
        "name": "Dept Head Cross-Org Test",
        "description": "Testing with department head from a different organization.",
        "organizationId": str(DEFAULT_ORG_ID), # Department is in the default org
        "department_head_id": str(person_in_other_org.id) # Head is from other_org
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_department_malformed_location_id(authenticated_test_client: AsyncClient, db_session: Session):
    department_data = {
        "name": "Location Malformed ID Test",
        "description": "Testing with a malformed UUID in location_ids.",
        "organizationId": str(DEFAULT_ORG_ID),
        "location_ids": ["not-a-valid-uuid-for-location"]
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_department_non_existent_location_id(authenticated_test_client: AsyncClient, db_session: Session):
    non_existent_loc_uuid = str(uuid.uuid4())
    department_data = {
        "name": "Location Non-Existent ID Test",
        "description": "Testing with a non-existent UUID in location_ids.",
        "organizationId": str(DEFAULT_ORG_ID),
        "location_ids": [non_existent_loc_uuid]
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_department_team_members_zero(authenticated_test_client: AsyncClient, db_session: Session):
    department_data = {
        "name": "Team Members Zero Test",
        "description": "Testing with number_of_team_members as zero.",
        "organizationId": str(DEFAULT_ORG_ID),
        "number_of_team_members": 0
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_department_team_members_negative(authenticated_test_client: AsyncClient, db_session: Session):
    department_data = {
        "name": "Team Members Negative Test",
        "description": "Testing with number_of_team_members as negative.",
        "organizationId": str(DEFAULT_ORG_ID),
        "number_of_team_members": -5
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_department_team_members_not_integer(authenticated_test_client: AsyncClient, db_session: Session):
    department_data = {
        "name": "Team Members Non-Integer Test",
        "description": "Testing with number_of_team_members as non-integer.",
        "organizationId": str(DEFAULT_ORG_ID),
        "number_of_team_members": "five"  # Non-integer
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_department_duplicate_name_conflict(authenticated_test_client: AsyncClient, db_session: Session):
    department_data = {
        "name": "Finance Department",
        "description": "Handles all financial matters.",
        "organizationId": str(DEFAULT_ORG_ID) # Use string UUID
    }
    # Create the first department
    response1 = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response1.status_code == status.HTTP_201_CREATED

    # Attempt to create a second department with the same name in the same organization
    department_data_duplicate = {
        "name": "Finance Department", # Same name
        "description": "Another finance department attempt.",
        "organizationId": str(DEFAULT_ORG_ID) # Same organization
    }
    response2 = await authenticated_test_client.post("/api/v1/departments/", json=department_data_duplicate)
    
    assert response2.status_code == status.HTTP_409_CONFLICT
    error_detail = response2.json()
    # Assuming the error message indicates a duplicate name for the given organization
    assert "already exists" in error_detail["detail"]

async def test_list_departments_empty(authenticated_test_client: AsyncClient, db_session: Session):
    # We query for departments belonging to an organization that is unlikely to have any.
    non_existent_org_id = str(uuid.uuid4())

    response = await authenticated_test_client.get(f"/api/v1/departments/?organization_id={non_existent_org_id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Assuming the endpoint returns a direct list when filtered and empty
    assert data == []
async def test_list_departments_with_data(authenticated_test_client: AsyncClient, db_session: Session):

    dept_data1 = {
        "name": "Marketing Department List Test", # Unique name
        "organizationId": str(DEFAULT_ORG_ID), 
        "description": "Handles marketing."
    }
    dept_data2 = {
        "name": "Sales Department List Test", # Unique name
        "organizationId": str(DEFAULT_ORG_ID), 
        "description": "Handles sales."
    }
    
    # Ensure these departments are created for the test
    await authenticated_test_client.post("/api/v1/departments/", json=dept_data1)
    await authenticated_test_client.post("/api/v1/departments/", json=dept_data2)
    
    response = await authenticated_test_client.get(f"/api/v1/departments/?organization_id={str(DEFAULT_ORG_ID)}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Filter for the specific departments created in this test for robust assertions
    test_dept_names = {dept_data1["name"], dept_data2["name"]}
    found_items = []
    # Assuming the endpoint returns a list directly if not paginated by default
    for item in data: # Changed from data["items"]
        if item["name"] in test_dept_names and item["organizationId"] == str(DEFAULT_ORG_ID):
            found_items.append(item)
            
    assert len(found_items) == 2
    # Removed assertions for createdBy and updatedBy as they are not in the response schema
    # Removed assertion for data["total"] as data is now a list.


async def test_update_department_empty_name(authenticated_test_client: AsyncClient, db_session: Session):
    # First, create a department to update
    dept_to_update = create_test_department(db_session, name="UpdateTargetEmptyName", organization_id=DEFAULT_ORG_ID)

    update_data = {
        "name": ""  # Empty name
    }
    response = await authenticated_test_client.put(f"/api/v1/departments/{dept_to_update.id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_update_department_name_too_long(authenticated_test_client: AsyncClient, db_session: Session):
    # First, create a department to update
    dept_to_update = create_test_department(db_session, name="UpdateTargetLongName", organization_id=DEFAULT_ORG_ID)
    long_name = "u" * 256  # Exceeds max_length of 255

    update_data = {
        "name": long_name
    }
    response = await authenticated_test_client.put(f"/api/v1/departments/{dept_to_update.id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_update_department_description_too_long(authenticated_test_client: AsyncClient, db_session: Session):
    # First, create a department to update
    dept_to_update = create_test_department(db_session, name="UpdateTargetLongDesc", organization_id=DEFAULT_ORG_ID)
    long_description = "d" * 1001  # Exceeds max_length of 1000

    update_data = {
        "description": long_description
    }
    response = await authenticated_test_client.put(f"/api/v1/departments/{dept_to_update.id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_update_department_malformed_department_head_id(authenticated_test_client: AsyncClient, db_session: Session):
    dept_to_update = create_test_department(db_session, name="UpdateTargetMalformedHeadId", organization_id=DEFAULT_ORG_ID)
    update_data = {"department_head_id": "not-a-uuid"}
    response = await authenticated_test_client.put(f"/api/v1/departments/{dept_to_update.id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_update_department_non_existent_department_head_id(authenticated_test_client: AsyncClient, db_session: Session):
    dept_to_update = create_test_department(db_session, name="UpdateTargetNonExistentHeadId", organization_id=DEFAULT_ORG_ID)
    non_existent_uuid = str(uuid.uuid4())
    update_data = {"department_head_id": non_existent_uuid}
    response = await authenticated_test_client.put(f"/api/v1/departments/{dept_to_update.id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_update_department_head_id_different_organization(authenticated_test_client: AsyncClient, db_session: Session):
    # Create a department in the default organization
    dept_to_update = create_test_department(db_session, name="UpdateTargetHeadDiffOrg", organization_id=DEFAULT_ORG_ID)
    # Create another organization and a person in it
    other_org = create_test_organization(db_session, name="Other Org For Dept Head Test", org_id=uuid.uuid4())
    person_in_other_org = create_test_person(db_session, email_prefix="other.org.head", organization_id=other_org.id)

    update_data = {"department_head_id": str(person_in_other_org.id)}
    response = await authenticated_test_client.put(f"/api/v1/departments/{dept_to_update.id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_get_department_by_id_success(authenticated_test_client: AsyncClient, db_session: Session):

    dept_data_in = {
        "name": "IT Department For Get Test", # Unique name for this test
        "description": "Handles all IT infrastructure.",
        "organizationId": str(DEFAULT_ORG_ID)
    }
    create_response = await authenticated_test_client.post("/api/v1/departments/", json=dept_data_in)
    assert create_response.status_code == status.HTTP_201_CREATED
    created_dept_json = create_response.json()
    created_dept_id = created_dept_json["id"] # This ID is already a string

    response = await authenticated_test_client.get(f"/api/v1/departments/{created_dept_id}")
    
    assert response.status_code == status.HTTP_200_OK
    dept_out = response.json()
    assert dept_out["id"] == created_dept_id
    assert dept_out["name"] == dept_data_in["name"]
    assert dept_out["description"] == dept_data_in["description"]
    assert dept_out["organizationId"] == str(DEFAULT_ORG_ID)
    # Removed assertions for createdBy and updatedBy as they are not in the response schema
    
    # Check for default relations if applicable (they should be None/empty if not set)
    assert "department_head" not in dept_out or dept_out["department_head"] is None 
    assert "locations" not in dept_out or dept_out["locations"] == []

async def test_get_department_by_id_not_found(authenticated_test_client: AsyncClient, db_session: Session): # Added db_session for consistency
    non_existent_id = str(uuid.uuid4())
    response = await authenticated_test_client.get(f"/api/v1/departments/{non_existent_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_get_department_by_id_with_relations(authenticated_test_client: AsyncClient, db_session: Session):
    # Use DEFAULT_ORG_ID for this test to align with authenticated client
    create_test_organization(db_session, name="Default Org For Dept Relations Test", org_id=DEFAULT_ORG_ID)

    # Create related entities within DEFAULT_ORG_ID
    dept_head = create_test_person(db_session, email_prefix="dept.head.relations", organization_id=DEFAULT_ORG_ID)
    dept_head_id_str = str(dept_head.id)
    dept_head_email_str = dept_head.email # Capture email
    loc1 = create_test_location(db_session, name="HQ Office Relations Test", organization_id=DEFAULT_ORG_ID)
    loc1_id_str = str(loc1.id)
    loc1_name_str = loc1.name # Capture name
    loc2 = create_test_location(db_session, name="Branch Office Relations Test", organization_id=DEFAULT_ORG_ID)
    loc2_id_str = str(loc2.id)
    loc2_name_str = loc2.name # Capture name

    dept_data_in = {
        "name": "Advanced Relations Department",
        "description": "Manages advanced projects with relations.",
        "organizationId": str(DEFAULT_ORG_ID),
        "department_head_id": dept_head_id_str,
        "location_ids": [loc1_id_str, loc2_id_str]
    }
    
    create_response = await authenticated_test_client.post("/api/v1/departments/", json=dept_data_in)
    assert create_response.status_code == status.HTTP_201_CREATED
    created_dept_json = create_response.json()
    created_dept_id = created_dept_json["id"]  # This ID is already a string from the API response

    # Fetch the department. Assuming the default GET response includes relations
    # if they are defined in the Pydantic response model.
    response = await authenticated_test_client.get(f"/api/v1/departments/{created_dept_id}")
    assert response.status_code == status.HTTP_200_OK
    dept_out = response.json()

    assert dept_out["id"] == created_dept_id
    assert dept_out["name"] == dept_data_in["name"]
    assert dept_out["organizationId"] == str(DEFAULT_ORG_ID)
    # Removed assertions for createdBy and updatedBy as they are not in the response schema

    # Check department head details
    assert dept_out["department_head"] is not None
    assert dept_out["department_head"]["id"] == dept_head_id_str
    assert "email" in dept_out["department_head"] # Ensure email is part of the nested schema
    assert dept_out["department_head"]["email"] == dept_head_email_str 

    # Check locations details
    assert "locations" in dept_out and dept_out["locations"] is not None
    assert len(dept_out["locations"]) == 2
    
    location_ids_out = {loc["id"] for loc in dept_out["locations"]} # IDs in response are strings
    assert loc1_id_str in location_ids_out
    assert loc2_id_str in location_ids_out
    
    location_names_out = {loc["name"] for loc in dept_out["locations"]} # Assuming name is in nested schema
    assert loc1_name_str in location_names_out
    assert loc2_name_str in location_names_out

async def test_update_department_success(authenticated_test_client: AsyncClient, db_session: Session):
    # Use DEFAULT_ORG_ID for this test to align with authenticated client
    create_test_organization(db_session, name="Default Org For Update Dept Success Test", org_id=DEFAULT_ORG_ID)

    # Initial department data
    dept_data_initial = {
        "name": "Initial Department Name",
        "description": "Initial description.",
        "organizationId": str(DEFAULT_ORG_ID)
    }
    create_response = await authenticated_test_client.post("/api/v1/departments/", json=dept_data_initial)
    assert create_response.status_code == status.HTTP_201_CREATED
    created_dept_json = create_response.json()
    department_id = created_dept_json["id"] # This is already a string

    # Data for updating the department
    update_data = {
        "name": "Updated Department Name",
        "description": "Updated description."
        # organizationId should not be updatable, or if it is, it needs specific testing.
        # For a simple success update, we only update name and description.
    }
    
    update_response = await authenticated_test_client.put(
        f"/api/v1/departments/{department_id}", 
        json=update_data
    )
    assert update_response.status_code == status.HTTP_200_OK
    updated_dept = update_response.json()

    assert updated_dept["id"] == department_id
    assert updated_dept["name"] == update_data["name"]
    assert updated_dept["description"] == update_data["description"]
    assert updated_dept["organizationId"] == str(DEFAULT_ORG_ID) # Should remain the same
    
    # Removed assertions for createdBy and updatedBy as they are not in the response schema
    
    # Verify that relations are not accidentally cleared if not provided in update
    # (This depends on PATCH vs PUT semantics if fully implemented, but for basic update,
    # existing relations should ideally persist if not mentioned in payload)
    # For this test, we assume no relations were set initially.
    assert "department_head" not in updated_dept or updated_dept["department_head"] is None
    assert "locations" not in updated_dept or updated_dept["locations"] == []

async def test_update_department_set_relations(authenticated_test_client: AsyncClient, db_session: Session):
    # Use DEFAULT_ORG_ID for this test to align with authenticated client
    # Ensure DEFAULT_ORG_ID exists, or create it if helper doesn't guarantee it.
    # For simplicity, assuming create_test_organization handles existing org_id or we ensure it's setup elsewhere.
    create_test_organization(db_session, name="Default Org For Set Relations Test", org_id=DEFAULT_ORG_ID)

    # Create entities to be used as relations within DEFAULT_ORG_ID
    new_dept_head = create_test_person(db_session, email_prefix="new.head.set", organization_id=DEFAULT_ORG_ID)
    new_dept_head_id_str = str(new_dept_head.id)
    new_dept_head_email_str = new_dept_head.email # Capture email before potential detachment
    new_loc1 = create_test_location(db_session, name="New Location Alpha Set", organization_id=DEFAULT_ORG_ID)
    new_loc1_id_str = str(new_loc1.id)
    new_loc2 = create_test_location(db_session, name="New Location Beta Set", organization_id=DEFAULT_ORG_ID)
    new_loc2_id_str = str(new_loc2.id)

    # Initial department data (no relations)
    dept_data_initial = {
        "name": "Department Before Setting Relations",
        "description": "No relations initially.",
        "organizationId": str(DEFAULT_ORG_ID)
    }
    create_response = await authenticated_test_client.post("/api/v1/departments/", json=dept_data_initial)
    assert create_response.status_code == status.HTTP_201_CREATED
    created_dept_json = create_response.json()
    department_id = created_dept_json["id"]

    # Verify initial state (no relations)
    assert created_dept_json.get("department_head") is None
    assert not created_dept_json.get("locations") # Empty list or not present

    # Data for updating the department to set relations
    update_data_set_relations = {
        "name": "Department After Setting Relations", # Optionally update name too
        "department_head_id": new_dept_head_id_str,
        "location_ids": [new_loc1_id_str, new_loc2_id_str]
    }
    
    update_response = await authenticated_test_client.put(
        f"/api/v1/departments/{department_id}", 
        json=update_data_set_relations
    )
    assert update_response.status_code == status.HTTP_200_OK
    updated_dept = update_response.json()

    assert updated_dept["id"] == department_id
    assert updated_dept["name"] == update_data_set_relations["name"]
    assert updated_dept["organizationId"] == str(DEFAULT_ORG_ID)
    # assert updated_dept["updatedBy"] == str(DEFAULT_USER_ID) # Removed updatedBy assertion

    # Verify department head is set
    assert updated_dept["department_head"] is not None
    assert updated_dept["department_head"]["id"] == new_dept_head_id_str
    assert updated_dept["department_head"]["email"] == new_dept_head_email_str

    # Verify locations are set
    assert "locations" in updated_dept and updated_dept["locations"] is not None
    assert len(updated_dept["locations"]) == 2
    location_ids_out = {loc["id"] for loc in updated_dept["locations"]}
    assert new_loc1_id_str in location_ids_out
    assert new_loc2_id_str in location_ids_out

async def test_update_department_change_relations(authenticated_test_client: AsyncClient, db_session: Session):
    # Use DEFAULT_ORG_ID for this test to align with authenticated client
    create_test_organization(db_session, name="Default Org For Change Relations Test", org_id=DEFAULT_ORG_ID)

    # Initial relations within DEFAULT_ORG_ID
    initial_head = create_test_person(db_session, email_prefix="initial.head.change", organization_id=DEFAULT_ORG_ID)
    initial_head_id_str = str(initial_head.id)
    initial_loc1 = create_test_location(db_session, name="Initial Location X Change", organization_id=DEFAULT_ORG_ID)
    initial_loc1_id_str = str(initial_loc1.id)
    initial_loc2 = create_test_location(db_session, name="Initial Location Y Change", organization_id=DEFAULT_ORG_ID)
    initial_loc2_id_str = str(initial_loc2.id)

    # New relations to change to, within DEFAULT_ORG_ID
    new_head = create_test_person(db_session, email_prefix="new.head.change", organization_id=DEFAULT_ORG_ID)
    new_head_id_str = str(new_head.id) # Get ID immediately
    new_head_email_str = new_head.email # Capture email before potential detachment
    new_loc_alpha = create_test_location(db_session, name="New Location Alpha Change", organization_id=DEFAULT_ORG_ID)
    new_loc_alpha_id_str = str(new_loc_alpha.id)
    new_loc_beta = create_test_location(db_session, name="New Location Beta Change", organization_id=DEFAULT_ORG_ID)
    new_loc_beta_id_str = str(new_loc_beta.id)

    # Initial department data with initial relations
    dept_data_initial = {
        "name": "Department Before Changing Relations",
        "organizationId": str(DEFAULT_ORG_ID),
        "department_head_id": initial_head_id_str,
        "location_ids": [initial_loc1_id_str, initial_loc2_id_str]
    }
    create_response = await authenticated_test_client.post("/api/v1/departments/", json=dept_data_initial)
    assert create_response.status_code == status.HTTP_201_CREATED
    created_dept_json = create_response.json()
    department_id = created_dept_json["id"]

    # Verify initial relations are set correctly
    assert created_dept_json["department_head"]["id"] == initial_head_id_str
    initial_loc_ids_out = {loc["id"] for loc in created_dept_json["locations"]}
    assert initial_loc1_id_str in initial_loc_ids_out
    assert initial_loc2_id_str in initial_loc_ids_out

    # Data for updating the department to change relations
    update_data_change_relations = {
        "name": "Department After Changing Relations", # Optionally update name
        "department_head_id": new_head_id_str,
        "location_ids": [new_loc_alpha_id_str, new_loc_beta_id_str]
    }
    
    update_response = await authenticated_test_client.put(
        f"/api/v1/departments/{department_id}", 
        json=update_data_change_relations
    )
    assert update_response.status_code == status.HTTP_200_OK
    updated_dept = update_response.json()

    assert updated_dept["id"] == department_id
    assert updated_dept["name"] == update_data_change_relations["name"]
    assert updated_dept["organizationId"] == str(DEFAULT_ORG_ID)
    # assert updated_dept["updatedBy"] == str(DEFAULT_USER_ID) # Removed updatedBy assertion

    # Verify department head is changed
    assert updated_dept["department_head"] is not None
    assert updated_dept["department_head"]["id"] == new_head_id_str
    assert updated_dept["department_head"]["email"] == new_head_email_str

    # Verify locations are changed
    assert "locations" in updated_dept and updated_dept["locations"] is not None
    assert len(updated_dept["locations"]) == 2
    location_ids_out = {loc["id"] for loc in updated_dept["locations"]}
    assert new_loc_alpha_id_str in location_ids_out
    assert new_loc_beta_id_str in location_ids_out
    # Ensure old locations are no longer associated
    assert initial_loc1_id_str not in location_ids_out
    assert initial_loc2_id_str not in location_ids_out

async def test_update_department_clear_relations(authenticated_test_client: AsyncClient, db_session: Session):
    # Ensure the DEFAULT_ORG_ID organization exists for the authenticated user
    # Department and its relations must be in DEFAULT_ORG_ID for the authenticated client to update it.
    test_org = create_test_organization(db_session, name="Default Org For Clear Relations Test", org_id=DEFAULT_ORG_ID)

    # Initial relations within DEFAULT_ORG_ID
    initial_head = create_test_person(db_session, email_prefix="head.to.clear", organization_id=DEFAULT_ORG_ID)
    initial_head_id_str = str(initial_head.id)
    initial_loc = create_test_location(db_session, name="Location To Clear", organization_id=DEFAULT_ORG_ID)
    initial_loc_id_str = str(initial_loc.id)

    # Initial department data with relations
    dept_data_initial = {
        "name": "Department Before Clearing Relations",
        "organizationId": str(DEFAULT_ORG_ID),
        "department_head_id": initial_head_id_str,
        "location_ids": [initial_loc_id_str]
    }
    create_response = await authenticated_test_client.post("/api/v1/departments/", json=dept_data_initial)
    assert create_response.status_code == status.HTTP_201_CREATED
    created_dept_json = create_response.json()
    department_id = created_dept_json["id"]

    # Verify initial relations are set
    assert created_dept_json["department_head"]["id"] == initial_head_id_str
    assert len(created_dept_json["locations"]) == 1
    assert created_dept_json["locations"][0]["id"] == initial_loc_id_str

    # Data for updating the department to clear relations
    # To clear a nullable foreign key like department_head_id, send `None` or `null`.
    # To clear a list relationship like locations, send an empty list `[]`.
    update_data_clear_relations = {
        "name": "Department After Clearing Relations", # Optionally update name
        "department_head_id": None,  # Explicitly set to None to clear
        "location_ids": []  # Explicitly set to empty list to clear
    }
    
    update_response = await authenticated_test_client.put(
        f"/api/v1/departments/{department_id}", 
        json=update_data_clear_relations
    )
    assert update_response.status_code == status.HTTP_200_OK
    updated_dept = update_response.json()

    assert updated_dept["id"] == department_id
    assert updated_dept["name"] == update_data_clear_relations["name"]
    assert updated_dept["organizationId"] == str(DEFAULT_ORG_ID) # Compare against the known DEFAULT_ORG_ID
    # assert updated_dept["updatedBy"] == str(DEFAULT_USER_ID) # Removed updatedBy assertion

    # Verify department head is cleared
    # The key "department_head" might still be in the response, but its value should be None.
    assert "department_head" in updated_dept 
    assert updated_dept["department_head"] is None

    # Verify locations are cleared
    # The key "locations" should be in the response, and its value should be an empty list.
    assert "locations" in updated_dept
    assert updated_dept["locations"] == []

async def test_update_department_not_found(authenticated_test_client: AsyncClient):
    non_existent_dept_id = str(uuid.uuid4())  # Generate a random UUID string
    update_data = {
        "name": "Ghost Department",
        "description": "This department does not exist."
    }
    
    response = await authenticated_test_client.put(
        f"/api/v1/departments/{non_existent_dept_id}", 
        json=update_data
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # Optionally, assert the error message if your API provides a consistent one
    # error_detail = response.json()
    # assert "not found" in error_detail["detail"].lower() 

async def test_update_department_invalid_relations(authenticated_test_client: AsyncClient, db_session: Session):
    # Define organization UUIDs upfront
    org1_id_str = str(uuid.uuid4())
    org2_id_str = str(uuid.uuid4())

    # Ensure organizations exist by passing UUID objects to the helper
    create_test_organization(db_session, name="Org 1 For Invalid Relations", org_id=uuid.UUID(org1_id_str))
    create_test_organization(db_session, name="Org 2 For Mismatched Relations", org_id=uuid.UUID(org2_id_str))

    # Create a department in Org1
    dept_data_initial = {
        "name": "Department to Test Invalid Relations",
        "organizationId": org1_id_str  # Use the string UUID directly
    }
    create_response = await authenticated_test_client.post("/api/v1/departments/", json=dept_data_initial)
    assert create_response.status_code == status.HTTP_201_CREATED
    department_id = create_response.json()["id"]

    # --- Test Case 1: Non-existent department_head_id ---
    non_existent_person_id = str(uuid.uuid4())
    update_data_invalid_head = {
        "department_head_id": non_existent_person_id
    }
    response_invalid_head = await authenticated_test_client.put(
        f"/api/v1/departments/{department_id}", 
        json=update_data_invalid_head
    )
    assert response_invalid_head.status_code == status.HTTP_404_NOT_FOUND

    # --- Test Case 2: Non-existent location_id in list ---
    # Create a valid location in Org1 and get its ID as a string
    valid_loc_org1 = create_test_location(db_session, name="Valid Loc Org1", organization_id=uuid.UUID(org1_id_str))
    valid_loc_org1_id_str = str(valid_loc_org1.id)
    non_existent_loc_id = str(uuid.uuid4())
    update_data_invalid_loc = {
        "location_ids": [valid_loc_org1_id_str, non_existent_loc_id]
    }
    response_invalid_loc = await authenticated_test_client.put(
        f"/api/v1/departments/{department_id}", 
        json=update_data_invalid_loc
    )
    assert response_invalid_loc.status_code == status.HTTP_404_NOT_FOUND

    # --- Test Case 3: department_head_id from a different organization (Org2) ---
    person_from_org2 = create_test_person(db_session, email_prefix="cross.org.head", organization_id=uuid.UUID(org2_id_str))
    person_from_org2_id_str = str(person_from_org2.id)
    update_data_cross_org_head = {
        "department_head_id": person_from_org2_id_str
    }
    response_cross_org_head = await authenticated_test_client.put(
        f"/api/v1/departments/{department_id}",
        json=update_data_cross_org_head
    )
    assert response_cross_org_head.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]
    
    # --- Test Case 4: location_id from a different organization (Org2) ---
    location_from_org2 = create_test_location(db_session, name="Cross Org Loc", organization_id=uuid.UUID(org2_id_str))
    location_from_org2_id_str = str(location_from_org2.id)
    update_data_cross_org_loc = {
        "location_ids": [location_from_org2_id_str]
    }
    response_cross_org_loc = await authenticated_test_client.put(
        f"/api/v1/departments/{department_id}",
        json=update_data_cross_org_loc
    )
    assert response_cross_org_loc.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]


async def test_delete_department_success_soft_delete(authenticated_test_client: AsyncClient, db_session: Session):
    # Ensure the DEFAULT_ORG_ID organization exists for the authenticated user
    create_test_organization(db_session, name="Default Org For Delete Test", org_id=DEFAULT_ORG_ID)

    # Department data, ensure it's created in DEFAULT_ORG_ID
    dept_data = {
        "name": "Department To Be Soft Deleted",
        "organizationId": str(DEFAULT_ORG_ID) # Use DEFAULT_ORG_ID
    }
    create_response = await authenticated_test_client.post("/api/v1/departments/", json=dept_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    created_dept_json = create_response.json()
    department_id = created_dept_json["id"]
    assert created_dept_json["isDeleted"] is False # Verify it's not deleted initially

    # Delete the department
    delete_response = await authenticated_test_client.delete(f"/api/v1/departments/{department_id}")
    assert delete_response.status_code == status.HTTP_200_OK
    deleted_dept_json = delete_response.json()
    assert deleted_dept_json["id"] == department_id
    assert deleted_dept_json["isDeleted"] is True
    assert deleted_dept_json["deleted_at"] is not None

    # Verify the department is not retrievable via GET by ID
    get_response = await authenticated_test_client.get(f"/api/v1/departments/{department_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

    # Verify it doesn't appear in the list for the default organization
    list_response = await authenticated_test_client.get("/api/v1/departments/") # This lists for current_user's org
    assert list_response.status_code == status.HTTP_200_OK
    departments = list_response.json()
    assert department_id not in [dept["id"] for dept in departments] 

async def test_delete_department_not_found_or_already_deleted(authenticated_test_client: AsyncClient, db_session: Session):
    # Case 1: Try to delete a non-existent department ID
    non_existent_dept_id = str(uuid.uuid4())
    response_non_existent = await authenticated_test_client.delete(
        f"/api/v1/departments/{non_existent_dept_id}"
    )
    assert response_non_existent.status_code == status.HTTP_404_NOT_FOUND

    # Case 2: Create a department, soft-delete it, then try to delete it again
    # Ensure the DEFAULT_ORG_ID organization exists
    create_test_organization(db_session, name="Default Org For Already Deleted Test", org_id=DEFAULT_ORG_ID)

    dept_data = {
        "name": "Department To Be Deleted Twice",
        "organizationId": str(DEFAULT_ORG_ID) # Use DEFAULT_ORG_ID
    }
    create_response = await authenticated_test_client.post("/api/v1/departments/", json=dept_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    department_id = create_response.json()["id"]

    # First delete (soft delete)
    first_delete_response = await authenticated_test_client.delete(f"/api/v1/departments/{department_id}")
    assert first_delete_response.status_code == status.HTTP_200_OK 
    assert first_delete_response.json()["isDeleted"] is True

    # Second delete attempt on an already soft-deleted department
    second_delete_response = await authenticated_test_client.delete(f"/api/v1/departments/{department_id}")
    assert second_delete_response.status_code == status.HTTP_404_NOT_FOUND

# --- Input Validation Tests ---

async def test_create_department_invalid_name_empty(authenticated_test_client: AsyncClient, db_session: Session):
    department_data = {
        "name": "", # Invalid: empty name
        "description": "Test department with empty name.",
        "organizationId": str(DEFAULT_ORG_ID)
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_department_invalid_name_too_long(authenticated_test_client: AsyncClient, db_session: Session):
    long_name = "a" * 256 # Invalid: name too long (max 255)
    department_data = {
        "name": long_name,
        "description": "Test department with very long name.",
        "organizationId": str(DEFAULT_ORG_ID)
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_update_department_invalid_name_empty(authenticated_test_client: AsyncClient, db_session: Session):
    # Create a department first
    dept_to_update = create_test_department(db_session, name="Original Name", organization_id=DEFAULT_ORG_ID)
    dept_id_str = str(dept_to_update.id)

    update_data = {
        "name": "" # Invalid: empty name
    }
    response = await authenticated_test_client.put(f"/api/v1/departments/{dept_id_str}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_update_department_invalid_name_too_long(authenticated_test_client: AsyncClient, db_session: Session):
    # Create a department first
    dept_to_update = create_test_department(db_session, name="Original Name", organization_id=DEFAULT_ORG_ID)
    dept_id_str = str(dept_to_update.id)
    long_name = "b" * 256 # Invalid: name too long

    update_data = {
        "name": long_name
    }
    response = await authenticated_test_client.put(f"/api/v1/departments/{dept_id_str}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_department_non_existent_organization_id(authenticated_test_client: AsyncClient, db_session: Session):
    non_existent_org_id = uuid.uuid4()
    department_data = {
        "name": "Department with Invalid Org",
        "description": "This department should not be created.",
        "organizationId": str(non_existent_org_id)
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    # Expect 422 if service layer catches it due to FK constraint before DB, or 404/400 if specific check exists
    # Pydantic itself won't know if the UUID exists, but the service/DB layer should reject it.
    # Common practice is 422 for semantically invalid data that passes schema validation but fails business/DB rules.
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY 

async def test_create_department_head_different_organization(authenticated_test_client: AsyncClient, db_session: Session):
    # org1 is DEFAULT_ORG_ID, used by authenticated_test_client implicitly for department creation context
    org2 = create_test_organization(db_session, name="Org Two For Head Test", org_id=uuid.uuid4())
    org2_id_str = str(org2.id)

    # Person in Org2
    person_in_org2 = create_test_person(db_session, email_prefix="head.in.org2", organization_id=org2.id)
    person_in_org2_id_str = str(person_in_org2.id)

    department_data = {
        "name": "Dept in Org1, Head in Org2",
        "organizationId": str(DEFAULT_ORG_ID), # Department is in Org1 (Default Org)
        "department_head_id": person_in_org2_id_str # Head is in Org2
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_update_department_head_different_organization(authenticated_test_client: AsyncClient, db_session: Session):
    # org1 is DEFAULT_ORG_ID
    org2 = create_test_organization(db_session, name="Org Two For Update Head Test", org_id=uuid.uuid4())
    org2_id_str = str(org2.id)

    # Department in Org1
    dept_in_org1 = create_test_department(db_session, name="Dept in Org1 To Update", organization_id=DEFAULT_ORG_ID)
    dept_in_org1_id_str = str(dept_in_org1.id)

    # Person in Org2
    person_in_org2 = create_test_person(db_session, email_prefix="newhead.in.org2", organization_id=org2.id)
    person_in_org2_id_str = str(person_in_org2.id)

    update_data = {
        "department_head_id": person_in_org2_id_str # Attempt to set head from Org2
    }
    response = await authenticated_test_client.put(f"/api/v1/departments/{dept_in_org1_id_str}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_department_location_different_organization(authenticated_test_client: AsyncClient, db_session: Session):
    org2 = create_test_organization(db_session, name="Org Two For Create Location Test", org_id=uuid.uuid4())

    # Location in Org2
    location_in_org2 = create_test_location(db_session, name="Location in Org2 for Create", organization_id=org2.id)
    location_in_org2_id_str = str(location_in_org2.id)

    department_data = {
        "name": "Dept in Org1, Location in Org2",
        "organizationId": str(DEFAULT_ORG_ID), # Department is in Org1 (Default Org)
        "location_ids": [location_in_org2_id_str] # Location is in Org2
    }
    response = await authenticated_test_client.post("/api/v1/departments/", json=department_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Optionally, check error detail if consistent
    # assert "One or more location IDs are invalid" in response.json()["detail"]

async def test_update_department_location_different_organization(authenticated_test_client: AsyncClient, db_session: Session):
    # Org1 is DEFAULT_ORG_ID
    org2 = create_test_organization(db_session, name="Org Two For Update Location Test", org_id=uuid.uuid4())

    # Department in Org1
    dept_in_org1 = create_test_department(db_session, name="Dept in Org1 To Update Location", organization_id=DEFAULT_ORG_ID)
    dept_in_org1_id_str = str(dept_in_org1.id)

    # Location in Org2
    location_in_org2 = create_test_location(db_session, name="Location in Org2 for Update", organization_id=org2.id)
    location_in_org2_id_str = str(location_in_org2.id)

    update_data = {
        "location_ids": [location_in_org2_id_str] # Attempt to link location from Org2
    }
    response = await authenticated_test_client.put(f"/api/v1/departments/{dept_in_org1_id_str}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Optionally, check error detail
    # assert "One or more location IDs are invalid" in response.json()["detail"]

# --- End Input Validation Tests ---


@pytest_asyncio.fixture(scope="function")
async def client_override_manager(test_client: AsyncClient):
    original_override = app.dependency_overrides.get(deps.get_current_user_placeholder)

    class Manager:
        async def set_user(self, user_id_for_auth: uuid.UUID) -> AsyncClient:
            def _override_get_current_user_for_specific_user(session: Session = Depends(deps.get_db)):
                db_user = session.get(PersonModel, user_id_for_auth, options=[
                    joinedload(PersonModel.roles).joinedload(RoleModel.permissions)
                ])
                if not db_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"User ID {user_id_for_auth} not found in override."
                    )
                if not db_user.isActive: # Check if user is active
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
                return db_user

            app.dependency_overrides[deps.get_current_user_placeholder] = _override_get_current_user_for_specific_user
            return test_client
        
        def reset_to_original(self):
            if original_override:
                app.dependency_overrides[deps.get_current_user_placeholder] = original_override
            elif deps.get_current_user_placeholder in app.dependency_overrides:
                del app.dependency_overrides[deps.get_current_user_placeholder]

    manager_instance = Manager()
    yield manager_instance

    # Final cleanup after the entire test function finishes
    if original_override:
        app.dependency_overrides[deps.get_current_user_placeholder] = original_override
    elif deps.get_current_user_placeholder in app.dependency_overrides:
        del app.dependency_overrides[deps.get_current_user_placeholder]


# --- RBAC Tests for Department API (FR 1.1, Test Case 1.1.12) ---

async def test_department_api_rbac(
    client_override_manager, # Renamed fixture
    db_session: Session,
    authenticated_test_client: AsyncClient # To create an initial department if needed
):
    # 0. Ensure default organization exists for users/roles
    org = create_test_organization(db_session, name="RBAC Test Org", org_id=DEFAULT_ORG_ID)
    org_id = org.id

    # 1. Define Permissions for Roles
    admin_dept_perms = [
        DepartmentPermissions.CREATE,
        DepartmentPermissions.READ,
        DepartmentPermissions.UPDATE,
        DepartmentPermissions.DELETE,
        DepartmentPermissions.LIST
    ]
    bcm_manager_dept_perms = admin_dept_perms # Same as admin for departments
    process_owner_dept_perms = [
        DepartmentPermissions.READ,
        DepartmentPermissions.LIST
    ]
    # No specific department perms for the 'no_access_role'

    # 2. Create Roles
    admin_role = create_test_role(db_session, name="RBAC Admin", organization_id=DEFAULT_ORG_ID, permission_names=admin_dept_perms)
    bcm_manager_role = create_test_role(db_session, name="RBAC BCM Manager", organization_id=DEFAULT_ORG_ID, permission_names=bcm_manager_dept_perms)
    process_owner_role = create_test_role(db_session, name="RBAC Process Owner", organization_id=DEFAULT_ORG_ID, permission_names=process_owner_dept_perms)
    no_access_role = create_test_role(db_session, name="RBAC No Dept Access", organization_id=DEFAULT_ORG_ID, permission_names=[]) # No department permissions

    # 3. Create Users with these Roles
    admin_user_obj = create_test_person(db_session, email_prefix="rbac.admin", organization_id=org_id, roles=[admin_role])
    admin_user_id = admin_user_obj.id
    bcm_manager_user_obj = create_test_person(db_session, email_prefix="rbac.bcmm", organization_id=org_id, roles=[bcm_manager_role])
    bcm_manager_user_id = bcm_manager_user_obj.id
    process_owner_user_obj = create_test_person(db_session, email_prefix="rbac.owner", organization_id=org_id, roles=[process_owner_role])
    process_owner_user_id = process_owner_user_obj.id
    no_access_user_obj = create_test_person(db_session, email_prefix="rbac.noaccess", organization_id=org_id, roles=[no_access_role])
    no_access_user_id = no_access_user_obj.id
    
    # 4. Test Scenarios - using user IDs to fetch fresh user objects later
    users_and_permissions = [
        ("Admin", admin_user_id, {"create": True, "read": True, "update": True, "delete": True, "list": True}),
        ("BCM Manager", bcm_manager_user_id, {"create": True, "read": True, "update": True, "delete": True, "list": True}),
        ("Process Owner", process_owner_user_id, {"create": False, "read": True, "update": False, "delete": False, "list": True}),
        ("No Access User", no_access_user_id, {"create": False, "read": False, "update": False, "delete": False, "list": False}),
    ]

    department_payload = {"name": "RBAC Test Department", "organizationId": str(org_id)}

    initial_dept_response = await authenticated_test_client.post("/api/v1/departments/", json=department_payload)
    assert initial_dept_response.status_code == status.HTTP_201_CREATED, f"Failed to create base department for RBAC test: {initial_dept_response.json()}"
    base_department_id = initial_dept_response.json()["id"]
    depts_to_cleanup_by_admin = [] # Initialize list here
    
    for role_name, current_user_id, perms in users_and_permissions:
        client = await client_override_manager.set_user(current_user_id)

        create_payload = {"name": f"Dept by {role_name.replace(' ', '')}", "organizationId": str(org_id)}
        response_create = await client.post("/api/v1/departments/", json=create_payload)
        if perms["create"]:
            assert response_create.status_code == status.HTTP_201_CREATED
            created_department_id_for_user = response_create.json()["id"]
            if perms["delete"]:
                del_resp = await client.delete(f"/api/v1/departments/{created_department_id_for_user}")
                assert del_resp.status_code == status.HTTP_200_OK
            else:
                depts_to_cleanup_by_admin.append(created_department_id_for_user)
        else:
            assert response_create.status_code == status.HTTP_403_FORBIDDEN

        response_list = await client.get("/api/v1/departments/")
        if perms["list"]:
            assert response_list.status_code == status.HTTP_200_OK
        else:
            assert response_list.status_code == status.HTTP_403_FORBIDDEN

        response_read = await client.get(f"/api/v1/departments/{base_department_id}")
        if perms["read"]:
            assert response_read.status_code == status.HTTP_200_OK
        else:
            assert response_read.status_code == status.HTTP_403_FORBIDDEN

        update_payload = {"description": f"Updated by {role_name}"}
        response_update = await client.put(f"/api/v1/departments/{base_department_id}", json=update_payload)
        if perms["update"]:
            assert response_update.status_code == status.HTTP_200_OK
        else:
            assert response_update.status_code == status.HTTP_403_FORBIDDEN

        # Test DELETE
        target_dept_id_for_delete = base_department_id
        temp_dept_id_for_delete_test = None
        if perms["delete"]:
            client_override_manager.reset_to_original() # Ensure admin for this creation
            temp_dept_payload = {"name": f"Temp Dept for {role_name} Delete", "organizationId": str(org_id)}
            resp_temp_create_admin = await authenticated_test_client.post("/api/v1/departments/", json=temp_dept_payload)
            assert resp_temp_create_admin.status_code == status.HTTP_201_CREATED, f"Admin failed to create temp_dept: {resp_temp_create_admin.json()}"
            temp_dept_id_for_delete_test = resp_temp_create_admin.json()["id"]
            target_dept_id_for_delete = temp_dept_id_for_delete_test
            # Set client back to current user for the actual delete operation
            client = await client_override_manager.set_user(current_user_id)
        
        response_delete = await client.delete(f"/api/v1/departments/{target_dept_id_for_delete}")
        if perms["delete"]:
            assert response_delete.status_code == status.HTTP_200_OK, f"{role_name} failed DELETE (status: {response_delete.status_code}) {response_delete.json()}"
        else:
            assert response_delete.status_code == status.HTTP_403_FORBIDDEN, f"{role_name} should NOT DELETE (status: {response_delete.status_code}) {response_delete.json()}"
            if target_dept_id_for_delete == base_department_id:
                client_override_manager.reset_to_original() # Reset to admin for this check
                check_still_exists = await authenticated_test_client.get(f"/api/v1/departments/{base_department_id}")
                assert check_still_exists.status_code == status.HTTP_200_OK, f"Base department check failed (status {check_still_exists.status_code}): {check_still_exists.json()}. Expected 200."

    # Final cleanup by admin
    client_override_manager.reset_to_original() # Ensure client is admin
    for dept_id_to_clean in depts_to_cleanup_by_admin:
        cleanup_resp = await authenticated_test_client.delete(f"/api/v1/departments/{dept_id_to_clean}")
        assert cleanup_resp.status_code == status.HTTP_200_OK, f"Admin failed to cleanup dept {dept_id_to_clean}: {cleanup_resp.json()}"
        
    # Final cleanup of the base department
    cleanup_response = await authenticated_test_client.delete(f"/api/v1/departments/{base_department_id}")
    assert cleanup_response.status_code == status.HTTP_200_OK, f"Failed to cleanup base department {base_department_id} in RBAC test: {cleanup_response.json()}"


async def test_create_department_with_same_name_as_soft_deleted(authenticated_test_client: AsyncClient, db_session: Session):
    create_test_organization(db_session, name="Default Org For Soft Delete Reuse", org_id=DEFAULT_ORG_ID)
    
    department_name = "Finance Department - Reuse Test"

    # Data for the first department
    dept_data_initial = {
        "name": department_name,
        "organizationId": str(DEFAULT_ORG_ID), # Use DEFAULT_ORG_ID
        "description": "Initial instance, to be soft-deleted."
    }
    # Create the first department
    create_response1 = await authenticated_test_client.post("/api/v1/departments/", json=dept_data_initial)
    assert create_response1.status_code == status.HTTP_201_CREATED
    department_id1 = create_response1.json()["id"]

    # Soft-delete the first department
    delete_response = await authenticated_test_client.delete(f"/api/v1/departments/{department_id1}")
    assert delete_response.status_code == status.HTTP_200_OK 
    assert delete_response.json()["isDeleted"] is True

    # Data for the second department with the same name
    dept_data_reuse = {
        "name": department_name, # Same name as the soft-deleted one
        "organizationId": str(DEFAULT_ORG_ID), # Use DEFAULT_ORG_ID
        "description": "New instance with the same name as a soft-deleted one."
    }
    # Attempt to create the second department with the same name
    create_response2 = await authenticated_test_client.post("/api/v1/departments/", json=dept_data_reuse)
    
    assert create_response2.status_code == status.HTTP_201_CREATED
    created_dept2_json = create_response2.json()
    department_id2 = created_dept2_json["id"]

    assert department_id2 != department_id1 
    assert created_dept2_json["name"] == department_name
    assert created_dept2_json["organizationId"] == str(DEFAULT_ORG_ID)
    assert created_dept2_json["isDeleted"] is False
