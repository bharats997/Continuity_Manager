# backend/app/tests/api/test_processes_api.py
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.schemas.processes import ProcessCreate, ProcessResponse
from app.models.domain.organizations import Organization as OrganizationModel
from app.models.domain.users import User as UserModel
from app.models.domain.departments import Department as DepartmentModel
from app.models.domain.locations import Location as LocationModel
from app.models.domain.applications import Application as ApplicationModel, ApplicationType
from app.models.domain.processes import Process as ProcessModel
from app.apis.deps import ProcessPermissions
from app.tests.helpers import (
    create_role_with_permissions_async,
    create_user_with_roles_async
)

# Assume create_test_organization_async and create_test_user_async are available 
# from conftest.py or a shared utility, or define them here if not.

# --- Helper Functions for Process Tests ---
async def create_test_department_async(db: AsyncSession, organization_id: uuid.UUID, name: str = "Test Department for Process") -> DepartmentModel:
    dept = DepartmentModel(
        id=uuid.uuid4(), 
        name=name, 
        organization_id=organization_id,
        # created_by_id and updated_by_id might be needed if your model enforces them
        # and they are not automatically handled by a fixture or service layer during test setup.
    )
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept

async def create_test_location_async(db: AsyncSession, organization_id: uuid.UUID, name: str = "Test Location for Process") -> LocationModel:
    loc = LocationModel(
        id=uuid.uuid4(),
        name=name,
        organization_id=organization_id,
        # created_by_id, updated_by_id if necessary
    )
    db.add(loc)
    await db.commit()
    await db.refresh(loc)
    return loc

async def create_test_application_async(db: AsyncSession, organization_id: uuid.UUID, name: str = "Test App for Process") -> ApplicationModel:
    app = ApplicationModel(
        id=uuid.uuid4(),
        name=name,
        organization_id=organization_id,
        type=ApplicationType.OWNED.value, # Example type
        # created_by_id, updated_by_id if necessary
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app

# --- Test Cases ---
@pytest.mark.asyncio
async def test_create_process_success(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None, "Test user must have an organization_id"

    # 1. Create necessary related entities
    department = await create_test_department_async(async_db_session, organization_id=org_id, name="Finance Process Dept")
    location1 = await create_test_location_async(async_db_session, organization_id=org_id, name="HQ Office for Process")
    app1 = await create_test_application_async(async_db_session, organization_id=org_id, name="ERP System for Process")
    
    process_owner = await async_db_session.get(UserModel, async_current_test_user.id) # Ensure user is in session
    if not process_owner: # Or create a specific process owner if different from current_user
        # This part depends on how create_test_user_async is structured or if you use async_current_test_user directly
        # For simplicity, using current_user as owner if they exist in the session
        # If create_test_user_async is available and you need a distinct owner:
        # process_owner = await create_test_user_async(async_db_session, organization_id=org_id, first_name_prefix="ProcOwner")
        pass

    process_payload = ProcessCreate(
        name="Quarterly Financial Reporting",
        description="Process for generating and reviewing quarterly financial reports.",
        department_id=department.id,
        process_owner_id=process_owner.id if process_owner else None,
        rto=1.5, # Example RTO in hours
        rpo=4.0, # Example RPO in hours
        criticality_level="High",
        manual_intervention_required=True,
        data_sensitivity_level="Confidential",
        location_ids=[location1.id],
        application_ids=[app1.id],
        process_dependency_ids=[]
    )

    response = await authenticated_test_client.post(
        "/api/v1/processes/", 
        json=process_payload.model_dump(mode='json')
    )

    assert response.status_code == 201, response.text
    response_data = response.json()
    
    assert response_data["name"] == process_payload.name
    assert response_data["description"] == process_payload.description
    assert response_data["department"]["id"] == str(department.id)
    if process_owner:
        assert response_data["process_owner"]["id"] == str(process_owner.id)
    assert response_data["rto"] == process_payload.rto
    assert response_data["rpo"] == process_payload.rpo
    assert response_data["criticality_level"] == process_payload.criticality_level
    assert response_data["manual_intervention_required"] == process_payload.manual_intervention_required
    assert response_data["data_sensitivity_level"] == process_payload.data_sensitivity_level
    
    assert len(response_data["locations"]) == 1
    assert response_data["locations"][0]["id"] == str(location1.id)
    assert len(response_data["applications"]) == 1
    assert response_data["applications"][0]["id"] == str(app1.id)
    assert len(response_data["process_dependencies"]) == 0
    assert len(response_data["dependent_on_processes"]) == 0

    # Verify in DB
    process_in_db = await async_db_session.get(ProcessModel, uuid.UUID(response_data["id"]))
    assert process_in_db is not None
    assert process_in_db.name == process_payload.name
    assert process_in_db.department_id == department.id


@pytest.mark.asyncio
async def test_create_process_minimal_data(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None, "Test user must have an organization_id"

    department = await create_test_department_async(async_db_session, organization_id=org_id, name="Minimal Process Dept")

    process_payload = ProcessCreate(
        name="Minimal Viable Process",
        department_id=department.id
        # All other fields are optional or have defaults
    )

    response = await authenticated_test_client.post(
        "/api/v1/processes/", 
        json=process_payload.model_dump(mode='json')
    )

    assert response.status_code == 201, response.text
    response_data = response.json()
    
    assert response_data["name"] == process_payload.name
    assert response_data["department"]["id"] == str(department.id)
    assert response_data["description"] is None # Default
    assert response_data["process_owner"] is None # Default
    assert response_data["rto"] is None # Default
    assert response_data["rpo"] is None # Default
    assert response_data["criticality_level"] == "Low" # Default from Pydantic model
    assert response_data["manual_intervention_required"] is False # Default
    assert response_data["data_sensitivity_level"] == "Public" # Default
    assert len(response_data["locations"]) == 0
    assert len(response_data["applications"]) == 0

    # Verify in DB
    process_in_db = await async_db_session.get(ProcessModel, uuid.UUID(response_data["id"]))
    assert process_in_db is not None
    assert process_in_db.name == process_payload.name
    assert process_in_db.department_id == department.id
    assert process_in_db.criticality_level == "Low"


@pytest.mark.asyncio
async def test_create_process_invalid_department_id(
    authenticated_test_client: AsyncClient, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None, "Test user must have an organization_id"

    non_existent_department_id = uuid.uuid4()

    process_payload = ProcessCreate(
        name="Process With Invalid Dept",
        department_id=non_existent_department_id
    )

    response = await authenticated_test_client.post(
        "/api/v1/processes/", 
        json=process_payload.model_dump(mode='json')
    )

    assert response.status_code == 404, response.text # Expecting 404 due to NotFoundException from service
    response_data = response.json()
    assert "not found" in response_data["detail"].lower()
    assert str(non_existent_department_id) in response_data["detail"]


@pytest.mark.asyncio
async def test_create_process_invalid_owner_id(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None, "Test user must have an organization_id"

    department = await create_test_department_async(async_db_session, organization_id=org_id, name="Dept for Invalid Owner Test")
    non_existent_owner_id = uuid.uuid4()

    process_payload = ProcessCreate(
        name="Process With Invalid Owner",
        department_id=department.id,
        process_owner_id=non_existent_owner_id
    )

    response = await authenticated_test_client.post(
        "/api/v1/processes/", 
        json=process_payload.model_dump(mode='json')
    )

    assert response.status_code == 404, response.text # Expecting 404 due to NotFoundException for user
    response_data = response.json()
    assert "user not found" in response_data["detail"].lower()
    assert str(non_existent_owner_id) in response_data["detail"]


@pytest.mark.asyncio
async def test_create_process_duplicate_name_in_department(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None, "Test user must have an organization_id"

    department = await create_test_department_async(async_db_session, organization_id=org_id, name="Dept for Duplicate Name Test")
    
    process_name = "Unique Process Name for Duplication Test"

    # Create the first process
    first_process_payload = ProcessCreate(
        name=process_name,
        department_id=department.id
    )
    response1 = await authenticated_test_client.post(
        "/api/v1/processes/", 
        json=first_process_payload.model_dump(mode='json')
    )
    assert response1.status_code == 201, f"Failed to create first process: {response1.text}"

    # Attempt to create a second process with the same name in the same department
    second_process_payload = ProcessCreate(
        name=process_name, # Same name
        department_id=department.id # Same department
    )
    response2 = await authenticated_test_client.post(
        "/api/v1/processes/", 
        json=second_process_payload.model_dump(mode='json')
    )

    assert response2.status_code == 400, response2.text # Expecting 400 due to BadRequestException (uniqueness constraint)
    response_data = response2.json()
    assert "already exists" in response_data["detail"].lower()
    assert process_name in response_data["detail"]


@pytest.mark.asyncio
async def test_create_process_invalid_location_id(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None
    department = await create_test_department_async(async_db_session, organization_id=org_id, name="Dept for Invalid Location Test")
    non_existent_location_id = uuid.uuid4()

    process_payload = ProcessCreate(
        name="Process With Invalid Location",
        department_id=department.id,
        location_ids=[non_existent_location_id]
    )

    response = await authenticated_test_client.post(
        "/api/v1/processes/", 
        json=process_payload.model_dump(mode='json')
    )

    assert response.status_code == 404, response.text
    response_data = response.json()
    assert "location(s) not found" in response_data["detail"].lower()
    assert str(non_existent_location_id) in response_data["detail"]


@pytest.mark.asyncio
async def test_create_process_invalid_application_id(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None
    department = await create_test_department_async(async_db_session, organization_id=org_id, name="Dept for Invalid App Test")
    non_existent_application_id = uuid.uuid4()

    process_payload = ProcessCreate(
        name="Process With Invalid Application",
        department_id=department.id,
        application_ids=[non_existent_application_id]
    )

    response = await authenticated_test_client.post(
        "/api/v1/processes/", 
        json=process_payload.model_dump(mode='json')
    )

    assert response.status_code == 404, response.text
    response_data = response.json()
    assert "application(s) not found" in response_data["detail"].lower()
    assert str(non_existent_application_id) in response_data["detail"]


@pytest.mark.asyncio
async def test_create_process_invalid_dependency_id(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None
    department = await create_test_department_async(async_db_session, organization_id=org_id, name="Dept for Invalid Dependency Test")
    non_existent_process_id = uuid.uuid4()

    process_payload = ProcessCreate(
        name="Process With Invalid Dependency",
        department_id=department.id,
        process_dependency_ids=[non_existent_process_id]
    )

    response = await authenticated_test_client.post(
        "/api/v1/processes/", 
        json=process_payload.model_dump(mode='json')
    )

    assert response.status_code == 404, response.text
    response_data = response.json()
    assert "process dependency(s) not found" in response_data["detail"].lower()
    assert str(non_existent_process_id) in response_data["detail"]

# --- Test Cases for GET /processes/{process_id} ---
@pytest.mark.asyncio
async def test_read_process_success(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None
    department = await create_test_department_async(async_db_session, organization_id=org_id, name="Dept for Read Test")
    
    # Create a process to read
    process_payload = ProcessCreate(
        name="Process to Read",
        department_id=department.id,
        description="A test process for reading."
    )
    create_response = await authenticated_test_client.post("/api/v1/processes/", json=process_payload.model_dump(mode='json'))
    assert create_response.status_code == 201
    created_process_data = create_response.json()
    process_id_to_read = created_process_data["id"]

    # Read the process
    read_response = await authenticated_test_client.get(f"/api/v1/processes/{process_id_to_read}")
    
    assert read_response.status_code == 200, read_response.text
    read_process_data = read_response.json()
    
    assert read_process_data["id"] == process_id_to_read
    assert read_process_data["name"] == process_payload.name
    assert read_process_data["description"] == process_payload.description
    assert read_process_data["department"]["id"] == str(department.id)


@pytest.mark.asyncio
async def test_read_process_not_found(
    authenticated_test_client: AsyncClient, 
    async_current_test_user: UserModel # Not strictly needed but good for context
):
    non_existent_process_id = uuid.uuid4()
    
    response = await authenticated_test_client.get(f"/api/v1/processes/{non_existent_process_id}")
    
    assert response.status_code == 404, response.text
    response_data = response.json()
    assert "process not found" in response_data["detail"].lower()


@pytest.mark.asyncio
async def test_read_process_different_organization(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel,
    # Need a way to create another org and user, or assume conftest provides a second client/user
    # For now, let's create another org and process directly in DB for this test
):
    # 1. Create a different organization
    other_org = OrganizationModel(id=uuid.uuid4(), name="Other Org for Read Test", industry="Testing")
    async_db_session.add(other_org)
    await async_db_session.commit()
    await async_db_session.refresh(other_org)

    # 2. Create a user in that other organization (needed for created_by_id if enforced by model)
    other_user = UserModel(
        id=uuid.uuid4(), 
        first_name="OtherUser", 
        last_name="ForProcess", 
        email="otheruser.process@example.com", 
        organization_id=other_org.id,
        password_hash="fakepassword"
    )
    async_db_session.add(other_user)
    await async_db_session.commit()
    await async_db_session.refresh(other_user)

    # 3. Create a department in the other organization
    other_department = DepartmentModel(
        id=uuid.uuid4(), 
        name="Other Org Department", 
        organization_id=other_org.id,
        created_by_id=other_user.id, # Assuming created_by_id is required
        updated_by_id=other_user.id  # Assuming updated_by_id is required
    )
    async_db_session.add(other_department)
    await async_db_session.commit()
    await async_db_session.refresh(other_department)

    # 4. Create a process in the other organization's department
    process_in_other_org = ProcessModel(
        id=uuid.uuid4(),
        name="Process in Other Org",
        department_id=other_department.id,
        created_by_id=other_user.id, # Assuming created_by_id is required
        updated_by_id=other_user.id  # Assuming updated_by_id is required
    )
    async_db_session.add(process_in_other_org)
    await async_db_session.commit()
    await async_db_session.refresh(process_in_other_org)

    # 5. Current authenticated user (from async_current_test_user.organization_id) tries to read it
    response = await authenticated_test_client.get(f"/api/v1/processes/{process_in_other_org.id}")
    
    assert response.status_code == 404, response.text # Should be 404 as it's not found for this user's org
    response_data = response.json()
    assert "process not found" in response_data["detail"].lower()

# UNIQUE_ANCHOR_FOR_PROCESS_LIST_TESTS

# --- Test Cases for GET /processes/ (List Processes) ---
@pytest.mark.asyncio
async def test_list_processes_empty(
    authenticated_test_client: AsyncClient, 
    async_current_test_user: UserModel # To ensure org context
):
    # This test assumes that for the current user's organization, either no processes exist
    # or that we are verifying the API's ability to return an empty list correctly.
    # For a truly isolated test of 'empty', one might need to ensure the org is new/empty.
    assert async_current_test_user.organization_id is not None
    
    # To ensure this test is robust, we can filter by a non-existent name or a new department
    # to guarantee an empty result for the purpose of checking the empty response structure.
    # However, a simple GET should also work if the org is indeed empty of processes.
    random_non_existent_filter = f"non_existent_filter_{uuid.uuid4().hex}"
    response = await authenticated_test_client.get(f"/api/v1/processes/?name={random_non_existent_filter}")
    
    assert response.status_code == 200, response.text
    response_data = response.json()
    assert response_data["total"] == 0
    assert len(response_data["items"]) == 0
    assert response_data["page"] == 1
    assert response_data["size"] == 10 # Default size

@pytest.mark.asyncio
async def test_list_processes_success(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None
    # Use a unique department name for this test to avoid conflicts
    dept_name = f"List Test Dept Success {uuid.uuid4().hex[:6]}"
    department = await create_test_department_async(async_db_session, organization_id=org_id, name=dept_name)

    # Create a couple of processes with unique names for this test
    proc_name1 = f"Process Alpha for List {uuid.uuid4().hex[:6]}"
    proc_name2 = f"Process Beta for List {uuid.uuid4().hex[:6]}"
    payload1 = ProcessCreate(name=proc_name1, department_id=department.id)
    payload2 = ProcessCreate(name=proc_name2, department_id=department.id)
    
    create_resp1 = await authenticated_test_client.post("/api/v1/processes/", json=payload1.model_dump(mode='json'))
    assert create_resp1.status_code == 201, create_resp1.text
    create_resp2 = await authenticated_test_client.post("/api/v1/processes/", json=payload2.model_dump(mode='json'))
    assert create_resp2.status_code == 201, create_resp2.text

    # List processes, specifically filtering by the department created for this test
    response = await authenticated_test_client.get(f"/api/v1/processes/?department_id={department.id}")
    assert response.status_code == 200, response.text
    response_data = response.json()

    assert response_data["total"] == 2
    assert len(response_data["items"]) == 2
    assert response_data["page"] == 1
    assert response_data["size"] == 10 # Default size, or could be 2 if total < default size

    names_in_response = {item["name"] for item in response_data["items"]}
    assert proc_name1 in names_in_response
    assert proc_name2 in names_in_response

@pytest.mark.asyncio
async def test_list_processes_pagination_and_sorting(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None
    dept_name = f"PagSort Dept List {uuid.uuid4().hex[:6]}"
    department = await create_test_department_async(async_db_session, organization_id=org_id, name=dept_name)

    base_name = f"PagSortProcess_{uuid.uuid4().hex[:6]}_"
    names_in_order = [f"{base_name}Alpha", f"{base_name}Bravo", f"{base_name}Charlie", f"{base_name}Delta"]
    
    for name in names_in_order: # Create in a specific order, though DB might not store it like that
        payload = ProcessCreate(name=name, department_id=department.id)
        resp = await authenticated_test_client.post("/api/v1/processes/", json=payload.model_dump(mode='json'))
        assert resp.status_code == 201, resp.text
    
    # Test pagination (page 2, size 2, sorted by name asc)
    # Filter by department_id to ensure we only get items from this test setup
    response_page2 = await authenticated_test_client.get(f"/api/v1/processes/?department_id={department.id}&page=2&size=2&sort_by=name&sort_order=asc")
    assert response_page2.status_code == 200, response_page2.text
    data_page2 = response_page2.json()
    
    # Expected order: Alpha, Bravo, Charlie, Delta
    # Page 1: Alpha, Bravo
    # Page 2: Charlie, Delta
    assert data_page2["total"] == 4
    assert len(data_page2["items"]) == 2
    assert data_page2["page"] == 2
    assert data_page2["size"] == 2
    assert data_page2["items"][0]["name"] == names_in_order[2] # Charlie
    assert data_page2["items"][1]["name"] == names_in_order[3] # Delta

    # Test sorting (desc by name, default page 1, default size 10)
    response_sorted_desc = await authenticated_test_client.get(f"/api/v1/processes/?department_id={department.id}&sort_by=name&sort_order=desc")
    assert response_sorted_desc.status_code == 200, response_sorted_desc.text
    data_sorted_desc = response_sorted_desc.json()
    assert data_sorted_desc["total"] == 4
    assert len(data_sorted_desc["items"]) == 4 # Since size is default 10 and total is 4
    assert data_sorted_desc["items"][0]["name"] == names_in_order[3] # Delta (desc)
    assert data_sorted_desc["items"][1]["name"] == names_in_order[2] # Charlie (desc)
    assert data_sorted_desc["items"][2]["name"] == names_in_order[1] # Bravo (desc)
    assert data_sorted_desc["items"][3]["name"] == names_in_order[0] # Alpha (desc)

@pytest.mark.asyncio
async def test_list_processes_filter_by_name(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None
    dept_name = f"Filter Name Dept List {uuid.uuid4().hex[:6]}"
    department = await create_test_department_async(async_db_session, organization_id=org_id, name=dept_name)
    unique_prefix = f"FilterTestName_{uuid.uuid4().hex[:6]}_"

    proc_name1 = f"{unique_prefix}Specific Process One"
    proc_name2 = f"{unique_prefix}Another Specific Process"
    proc_name3 = f"{unique_prefix}General Process"

    await authenticated_test_client.post("/api/v1/processes/", json=ProcessCreate(name=proc_name1, department_id=department.id).model_dump(mode='json'))
    await authenticated_test_client.post("/api/v1/processes/", json=ProcessCreate(name=proc_name2, department_id=department.id).model_dump(mode='json'))
    await authenticated_test_client.post("/api/v1/processes/", json=ProcessCreate(name=proc_name3, department_id=department.id).model_dump(mode='json'))

    # Filter by a part of the name, also by department to ensure isolation
    response = await authenticated_test_client.get(f"/api/v1/processes/?department_id={department.id}&name=Specific Process")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    names_in_response = {item["name"] for item in data["items"]}
    assert proc_name1 in names_in_response
    assert proc_name2 in names_in_response
    assert proc_name3 not in names_in_response

@pytest.mark.asyncio
async def test_list_processes_filter_by_department(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None
    dept1_name = f"Finance Dept for Filter List {uuid.uuid4().hex[:4]}"
    dept2_name = f"HR Dept for Filter List {uuid.uuid4().hex[:4]}"
    dept1 = await create_test_department_async(async_db_session, organization_id=org_id, name=dept1_name)
    dept2 = await create_test_department_async(async_db_session, organization_id=org_id, name=dept2_name)
    
    proc_name_prefix = f"FilterDeptProc_{uuid.uuid4().hex[:4]}_"

    # Processes for dept1
    proc1_dept1 = f"{proc_name_prefix}Finance Proc 1"
    proc2_dept1 = f"{proc_name_prefix}Finance Proc 2"
    # Process for dept2
    proc1_dept2 = f"{proc_name_prefix}HR Proc 1"

    await authenticated_test_client.post("/api/v1/processes/", json=ProcessCreate(name=proc1_dept1, department_id=dept1.id).model_dump(mode='json'))
    await authenticated_test_client.post("/api/v1/processes/", json=ProcessCreate(name=proc1_dept2, department_id=dept2.id).model_dump(mode='json'))
    await authenticated_test_client.post("/api/v1/processes/", json=ProcessCreate(name=proc2_dept1, department_id=dept1.id).model_dump(mode='json'))

    response = await authenticated_test_client.get(f"/api/v1/processes/?department_id={dept1.id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    names_in_response = {item["name"] for item in data["items"]}
    assert proc1_dept1 in names_in_response
    assert proc2_dept1 in names_in_response
    assert proc1_dept2 not in names_in_response
    for item in data["items"]:
        assert item["department"]["id"] == str(dept1.id)

@pytest.mark.asyncio
async def test_list_processes_filter_by_criticality(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None
    dept_name = f"Criticality Filter Dept List {uuid.uuid4().hex[:4]}"
    department = await create_test_department_async(async_db_session, organization_id=org_id, name=dept_name)
    crit_prefix = f"CritFilter_{uuid.uuid4().hex[:4]}_"

    proc_high1 = f"{crit_prefix}High Crit Proc"
    proc_med1 = f"{crit_prefix}Medium Crit Proc"
    proc_high2 = f"{crit_prefix}Another High Crit Proc"

    await authenticated_test_client.post("/api/v1/processes/", json=ProcessCreate(name=proc_high1, department_id=department.id, criticality_level="High").model_dump(mode='json'))
    await authenticated_test_client.post("/api/v1/processes/", json=ProcessCreate(name=proc_med1, department_id=department.id, criticality_level="Medium").model_dump(mode='json'))
    await authenticated_test_client.post("/api/v1/processes/", json=ProcessCreate(name=proc_high2, department_id=department.id, criticality_level="High").model_dump(mode='json'))

    # Filter by criticality AND department_id for isolation
    response = await authenticated_test_client.get(f"/api/v1/processes/?department_id={department.id}&criticality_level=High")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    names_in_response = {item["name"] for item in data["items"]}
    assert proc_high1 in names_in_response
    assert proc_high2 in names_in_response
    assert proc_med1 not in names_in_response
    for item in data["items"]:
        assert item["criticality_level"] == "High"

# --- Test Cases for PUT /processes/{process_id} (Update Process) ---
@pytest.mark.asyncio
async def test_update_process_success(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None
    department = await create_test_department_async(async_db_session, organization_id=org_id, name=f"Update Test Dept {uuid.uuid4().hex[:6]}")
    process_owner_user = await async_db_session.get(UserModel, async_current_test_user.id) # Use current user as initial owner

    # Initial M2M entities
    loc1 = await create_test_location_async(async_db_session, organization_id=org_id, name=f"UpdateLoc1 {uuid.uuid4().hex[:4]}")
    app1 = await create_test_application_async(async_db_session, organization_id=org_id, name=f"UpdateApp1 {uuid.uuid4().hex[:4]}")

    # Create a process to update
    initial_payload = ProcessCreate(
        name=f"Initial Process for Update {uuid.uuid4().hex[:6]}",
        department_id=department.id,
        process_owner_id=process_owner_user.id if process_owner_user else None,
        description="Initial description",
        rto=1.0,
        rpo=2.0,
        criticality_level="Medium",
        location_ids=[loc1.id],
        application_ids=[app1.id]
    )
    create_response = await authenticated_test_client.post("/api/v1/processes/", json=initial_payload.model_dump(mode='json'))
    assert create_response.status_code == 201, create_response.text
    process_id_to_update = create_response.json()["id"]

    # New M2M entities for update
    loc2 = await create_test_location_async(async_db_session, organization_id=org_id, name=f"UpdateLoc2 {uuid.uuid4().hex[:4]}")
    app2 = await create_test_application_async(async_db_session, organization_id=org_id, name=f"UpdateApp2 {uuid.uuid4().hex[:4]}")
    
    # Create another process to be a dependency
    dependent_proc_payload = ProcessCreate(name=f"Dependent Process for Update {uuid.uuid4().hex[:6]}", department_id=department.id)
    dep_create_resp = await authenticated_test_client.post("/api/v1/processes/", json=dependent_proc_payload.model_dump(mode='json'))
    assert dep_create_resp.status_code == 201
    dependent_process_id = dep_create_resp.json()["id"]

    update_payload_data = {
        "name": f"Updated Process Name {uuid.uuid4().hex[:6]}",
        "description": "Updated process description.",
        "rto": 2.5,
        "rpo": 5.0,
        "criticality_level": "High",
        "manual_intervention_required": True,
        "data_sensitivity_level": "Restricted",
        "location_ids": [loc2.id], # Replace loc1 with loc2
        "application_ids": [app1.id, app2.id], # Keep app1, add app2
        "process_dependency_ids": [dependent_process_id] # Add a dependency
    }

    response = await authenticated_test_client.put(
        f"/api/v1/processes/{process_id_to_update}", 
        json=update_payload_data
    )
    assert response.status_code == 200, response.text
    updated_data = response.json()

    assert updated_data["name"] == update_payload_data["name"]
    assert updated_data["description"] == update_payload_data["description"]
    assert updated_data["rto"] == update_payload_data["rto"]
    assert updated_data["rpo"] == update_payload_data["rpo"]
    assert updated_data["criticality_level"] == update_payload_data["criticality_level"]
    assert updated_data["manual_intervention_required"] == update_payload_data["manual_intervention_required"]
    assert updated_data["data_sensitivity_level"] == update_payload_data["data_sensitivity_level"]
    
    assert len(updated_data["locations"]) == 1
    assert updated_data["locations"][0]["id"] == str(loc2.id)
    assert len(updated_data["applications"]) == 2
    app_ids_in_response = {app["id"] for app in updated_data["applications"]}
    assert str(app1.id) in app_ids_in_response
    assert str(app2.id) in app_ids_in_response
    assert len(updated_data["process_dependencies"]) == 1
    assert updated_data["process_dependencies"][0]["id"] == str(dependent_process_id)

    # Verify in DB
    process_in_db = await async_db_session.get(ProcessModel, uuid.UUID(process_id_to_update))
    await async_db_session.refresh(process_in_db, relationship_names=["locations", "applications", "process_dependencies"]) # Eager load for verification
    assert process_in_db is not None
    assert process_in_db.name == update_payload_data["name"]
    db_loc_ids = {loc.id for loc in process_in_db.locations}
    assert loc2.id in db_loc_ids
    assert loc1.id not in db_loc_ids
    db_app_ids = {app.id for app in process_in_db.applications}
    assert app1.id in db_app_ids and app2.id in db_app_ids
    db_dep_ids = {dep.id for dep in process_in_db.process_dependencies}
    assert dependent_process_id in db_dep_ids

@pytest.mark.asyncio
async def test_update_process_clear_m2m_relationships(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None
    department = await create_test_department_async(async_db_session, organization_id=org_id, name=f"ClearM2MDept {uuid.uuid4().hex[:6]}")
    loc1 = await create_test_location_async(async_db_session, organization_id=org_id, name=f"ClearLoc1 {uuid.uuid4().hex[:4]}")
    app1 = await create_test_application_async(async_db_session, organization_id=org_id, name=f"ClearApp1 {uuid.uuid4().hex[:4]}")

    initial_payload = ProcessCreate(
        name=f"Process for Clearing M2M {uuid.uuid4().hex[:6]}",
        department_id=department.id,
        location_ids=[loc1.id],
        application_ids=[app1.id]
    )
    create_response = await authenticated_test_client.post("/api/v1/processes/", json=initial_payload.model_dump(mode='json'))
    assert create_response.status_code == 201
    process_id = create_response.json()["id"]

    update_payload = {
        "location_ids": [],
        "application_ids": [],
        "process_dependency_ids": []
    }
    response = await authenticated_test_client.put(f"/api/v1/processes/{process_id}", json=update_payload)
    assert response.status_code == 200, response.text
    updated_data = response.json()

    assert len(updated_data["locations"]) == 0
    assert len(updated_data["applications"]) == 0
    assert len(updated_data["process_dependencies"]) == 0

@pytest.mark.asyncio
async def test_update_process_not_found(
    authenticated_test_client: AsyncClient, 
    async_current_test_user: UserModel
):
    non_existent_process_id = uuid.uuid4()
    update_payload = {"name": "Attempt to update non-existent"}
    response = await authenticated_test_client.put(
        f"/api/v1/processes/{non_existent_process_id}", 
        json=update_payload
    )
    assert response.status_code == 404, response.text
    assert "not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_update_process_invalid_department_id(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    department = await create_test_department_async(async_db_session, organization_id=org_id, name=f"UpdateInvalidDept Original {uuid.uuid4().hex[:6]}")
    initial_payload = ProcessCreate(name=f"Process for Invalid Dept Update {uuid.uuid4().hex[:6]}", department_id=department.id)
    create_response = await authenticated_test_client.post("/api/v1/processes/", json=initial_payload.model_dump(mode='json'))
    assert create_response.status_code == 201
    process_id = create_response.json()["id"]

    non_existent_dept_id = uuid.uuid4()
    update_payload = {"department_id": str(non_existent_dept_id)}
    response = await authenticated_test_client.put(f"/api/v1/processes/{process_id}", json=update_payload)
    assert response.status_code == 404, response.text # Department not found
    assert "department not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_update_process_name_uniqueness_violation(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    department = await create_test_department_async(async_db_session, organization_id=org_id, name=f"UpdateUniquenessDept {uuid.uuid4().hex[:6]}")
    
    existing_process_name = f"Existing Process Name {uuid.uuid4().hex[:6]}"
    payload1 = ProcessCreate(name=existing_process_name, department_id=department.id)
    await authenticated_test_client.post("/api/v1/processes/", json=payload1.model_dump(mode='json'))

    payload2 = ProcessCreate(name=f"Process To Be Updated {uuid.uuid4().hex[:6]}", department_id=department.id)
    create_response2 = await authenticated_test_client.post("/api/v1/processes/", json=payload2.model_dump(mode='json'))
    assert create_response2.status_code == 201
    process_to_update_id = create_response2.json()["id"]

    update_payload = {"name": existing_process_name} # Try to update to the existing name
    response = await authenticated_test_client.put(f"/api/v1/processes/{process_to_update_id}", json=update_payload)
    assert response.status_code == 400, response.text # Or 409, based on service impl.
    assert "already exists" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_update_process_different_organization(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    # Create a process in another organization directly in DB
    other_org = OrganizationModel(id=uuid.uuid4(), name=f"Other Org Update {uuid.uuid4().hex[:4]}", industry="Other")
    async_db_session.add(other_org)
    # Create a user for the other org (needed for created_by_id)
    other_user = UserModel(id=uuid.uuid4(), first_name="Other", last_name="User", email=f"other{uuid.uuid4().hex[:4]}@example.com", organization_id=other_org.id, password_hash="hash")
    async_db_session.add(other_user)
    await async_db_session.commit()
    await async_db_session.refresh(other_org)
    await async_db_session.refresh(other_user)

    other_dept = DepartmentModel(id=uuid.uuid4(), name=f"Other Dept Update {uuid.uuid4().hex[:4]}", organization_id=other_org.id, created_by_id=other_user.id, updated_by_id=other_user.id)
    async_db_session.add(other_dept)
    await async_db_session.commit()
    await async_db_session.refresh(other_dept)

    process_in_other_org = ProcessModel(
        id=uuid.uuid4(), name=f"Process in Other Org Update {uuid.uuid4().hex[:4]}", 
        department_id=other_dept.id, 
        created_by_id=other_user.id, updated_by_id=other_user.id
    )
    async_db_session.add(process_in_other_org)
    await async_db_session.commit()
    await async_db_session.refresh(process_in_other_org)

    update_payload = {"name": "Attempted Update Across Orgs"}
    response = await authenticated_test_client.put(f"/api/v1/processes/{process_in_other_org.id}", json=update_payload)
    assert response.status_code == 404, response.text # Should be not found for current user's org
    assert "not found" in response.json()["detail"].lower()

# --- Test Cases for DELETE /processes/{process_id} (Delete Process) ---
@pytest.mark.asyncio
async def test_delete_process_success(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    assert org_id is not None
    department = await create_test_department_async(async_db_session, organization_id=org_id, name=f"Delete Test Dept {uuid.uuid4().hex[:6]}")

    payload = ProcessCreate(name=f"Process to Delete {uuid.uuid4().hex[:6]}", department_id=department.id)
    create_response = await authenticated_test_client.post("/api/v1/processes/", json=payload.model_dump(mode='json'))
    assert create_response.status_code == 201, create_response.text
    process_id_to_delete = create_response.json()["id"]

    # Ensure it's not deleted before the call
    process_before_delete = await async_db_session.get(ProcessModel, uuid.UUID(process_id_to_delete))
    assert process_before_delete is not None
    assert process_before_delete.is_deleted is False

    delete_response = await authenticated_test_client.delete(f"/api/v1/processes/{process_id_to_delete}")
    assert delete_response.status_code == 200, delete_response.text # Or 204 if no content is returned
    # Assuming 200 with a success message as per current API design for other deletes
    delete_response_data = delete_response.json()
    assert "successfully deleted" in delete_response_data["message"].lower()
    assert delete_response_data["process_id"] == process_id_to_delete

    # Verify soft delete in DB
    process_in_db = await async_db_session.get(ProcessModel, uuid.UUID(process_id_to_delete))
    assert process_in_db is not None # Record still exists
    assert process_in_db.is_deleted is True
    assert process_in_db.deleted_at is not None

    # Attempting to GET the soft-deleted process should result in 404
    get_response = await authenticated_test_client.get(f"/api/v1/processes/{process_id_to_delete}")
    assert get_response.status_code == 404, get_response.text

@pytest.mark.asyncio
async def test_delete_process_not_found(
    authenticated_test_client: AsyncClient, 
    async_current_test_user: UserModel
):
    non_existent_process_id = uuid.uuid4()
    response = await authenticated_test_client.delete(f"/api/v1/processes/{non_existent_process_id}")
    assert response.status_code == 404, response.text
    assert "not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_delete_process_already_deleted(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    org_id = async_current_test_user.organization_id
    department = await create_test_department_async(async_db_session, organization_id=org_id, name=f"Already Deleted Dept {uuid.uuid4().hex[:6]}")
    payload = ProcessCreate(name=f"Process for Double Delete Test {uuid.uuid4().hex[:6]}", department_id=department.id)
    create_response = await authenticated_test_client.post("/api/v1/processes/", json=payload.model_dump(mode='json'))
    assert create_response.status_code == 201
    process_id = create_response.json()["id"]

    # First delete
    await authenticated_test_client.delete(f"/api/v1/processes/{process_id}")
    
    # Second delete attempt
    response = await authenticated_test_client.delete(f"/api/v1/processes/{process_id}")
    assert response.status_code == 404, response.text # Service should treat it as not found for deletion purposes
    assert "already deleted or not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_delete_process_different_organization(
    authenticated_test_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_current_test_user: UserModel
):
    # Create a process in another organization directly in DB
    other_org = OrganizationModel(id=uuid.uuid4(), name=f"Other Org Delete {uuid.uuid4().hex[:4]}", industry="Other")
    async_db_session.add(other_org)
    other_user = UserModel(id=uuid.uuid4(), first_name="OtherDel", last_name="UserDel", email=f"otherdel{uuid.uuid4().hex[:4]}@example.com", organization_id=other_org.id, password_hash="hash")
    async_db_session.add(other_user)
    await async_db_session.commit()
    await async_db_session.refresh(other_org)
    await async_db_session.refresh(other_user)

    other_dept = DepartmentModel(id=uuid.uuid4(), name=f"Other Dept Delete {uuid.uuid4().hex[:4]}", organization_id=other_org.id, created_by_id=other_user.id, updated_by_id=other_user.id)
    async_db_session.add(other_dept)
    await async_db_session.commit()
    await async_db_session.refresh(other_dept)

    process_in_other_org = ProcessModel(
        id=uuid.uuid4(), name=f"Process in Other Org Delete {uuid.uuid4().hex[:4]}", 
        department_id=other_dept.id, 
        created_by_id=other_user.id, updated_by_id=other_user.id
    )
    async_db_session.add(process_in_other_org)
    await async_db_session.commit()
    await async_db_session.refresh(process_in_other_org)

    response = await authenticated_test_client.delete(f"/api/v1/processes/{process_in_other_org.id}")
    assert response.status_code == 404, response.text
    assert "not found" in response.json()["detail"].lower()

