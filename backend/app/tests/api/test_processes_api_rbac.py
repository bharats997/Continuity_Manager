# backend/app/tests/api/test_processes_api_rbac.py
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.schemas.processes import ProcessCreate, ProcessUpdate
from app.models.domain.users import User as UserModel
from app.models.domain.departments import Department as DepartmentModel
from app.models.domain.processes import Process as ProcessModel
from app.models.domain.locations import Location as LocationModel # Added for location test
from app.models.domain.organizations import Organization as OrganizationModel # Added for cross-org test
from app.models.domain.applications import Application as ApplicationModel
from app.apis.deps import ProcessPermissions
from app.tests.helpers import (
    create_role_with_permissions_async,
    create_user_with_roles_async,
)

# --- Helper Functions --- 
# TODO: Consider moving shared helpers like create_test_department_async to a common utility or conftest
async def create_test_department_async(db: AsyncSession, organization_id: uuid.UUID, name: str = "Test Department for Process RBAC") -> DepartmentModel:
    dept = DepartmentModel(
        id=uuid.uuid4(), 
        name=name, 
        organization_id=organization_id,
    )
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept

# Helper to create a basic process payload
def _get_base_process_payload(department_id: uuid.UUID, organization_id: uuid.UUID, owner_id: Optional[uuid.UUID] = None) -> dict:
    return ProcessCreate(
        name=f"RBAC Test Process {uuid.uuid4().hex[:6]}",
        description="Process for RBAC testing.",
        department_id=department_id,
        organization_id=organization_id,
        process_owner_id=owner_id, # Optional, can be None
        rto=1.0,
        rpo=1.0,
        criticality_level="Medium"
    ).model_dump(mode='json')

# --- RBAC Test Cases for Process API --- 

@pytest.mark.asyncio
async def test_rbac_create_process_with_permission(
    async_client_authenticated_as_user_factory, 
    async_db_session: AsyncSession,
    async_default_app_user: UserModel # Used for org_id context from conftest
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: Create a role with 'process:create' permission
    creator_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"ProcessCreatorRole_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE], organization_id=org_id
    )

    # 2. Setup: Create a user with this role
    user_with_create_perm = await create_user_with_roles_async(
        db_session=async_db_session, email=f"creator_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[creator_role.name], organization_id=org_id
    )

    # 3. Get client for this user
    async for authed_client in async_client_authenticated_as_user_factory(user_with_create_perm):
        # 4. Prepare data for process creation
        department = await create_test_department_async(async_db_session, organization_id=org_id, name=f"RBAC Dept Create {uuid.uuid4().hex[:6]}")
        
        # Verify department exists in current session before API call
        queried_department = await async_db_session.get(DepartmentModel, department.id)
        assert queried_department is not None, "Department not found in session after creation"
        assert queried_department.id == department.id, "Queried department ID mismatch"
        assert queried_department.organization_id == org_id, "Queried department org ID mismatch"

        process_payload = _get_base_process_payload(department_id=department.id, organization_id=org_id, owner_id=user_with_create_perm.id)

        # 5. Action: Attempt to create a process
        response = await authed_client.post("/api/v1/processes/", json=process_payload)

        # 6. Assert: Expect success (201 Created)
        assert response.status_code == 201, response.text
        response_data = response.json()
        assert response_data["name"] == process_payload["name"]
        assert "department" in response_data, "'department' key missing in response"
        assert response_data["department"]["organization_id"] == str(org_id), "Organization ID mismatch"

        # Verify in DB
        process_in_db = await async_db_session.get(ProcessModel, uuid.UUID(response_data["id"]))
        assert process_in_db is not None
        assert process_in_db.name == process_payload["name"]

@pytest.mark.asyncio
async def test_rbac_create_process_without_permission(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel # Used for org_id context from conftest
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: Create a role with a different permission (e.g., 'process:read')
    reader_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"ProcessReaderRole_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.READ], organization_id=org_id
    )

    # 2. Setup: Create a user with this 'reader' role
    user_without_create_perm = await create_user_with_roles_async(
        db_session=async_db_session, email=f"reader_no_create_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[reader_role.name], organization_id=org_id
    )

    # 3. Get client for this user
    async for authed_client in async_client_authenticated_as_user_factory(user_without_create_perm):
        # 4. Prepare data for process creation
        department = await create_test_department_async(async_db_session, organization_id=org_id, name=f"RBAC Dept NoCreate {uuid.uuid4().hex[:6]}")
        process_payload = _get_base_process_payload(department.id, user_without_create_perm.id)

        # 5. Action: Attempt to create a process
        response = await authed_client.post("/api/v1/processes/", json=process_payload)

        # 6. Assert: Expect 403 Forbidden
        assert response.status_code == 403, response.text
        response_data = response.json()
        assert "do not have the required permission" in response_data["detail"].lower()
        assert ProcessPermissions.CREATE in response_data["detail"]

@pytest.mark.asyncio
async def test_rbac_create_process_with_no_relevant_permissions(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel # Used for org_id context from conftest
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: Create a role with no process-related permissions
    # Ensure a dummy permission exists that is not process:create, to assign to the role.
    
    no_process_perms_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"NoProcessPermsRole_{uuid.uuid4().hex[:4]}", permissions_names=["dummy:permission_rbac_test_process"], organization_id=org_id
    )

    # 2. Setup: Create a user with this role
    user_with_no_perms = await create_user_with_roles_async(
        db_session=async_db_session, email=f"noperms_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[no_process_perms_role.name], organization_id=org_id
    )
    
    # 3. Get client for this user
    async for authed_client in async_client_authenticated_as_user_factory(user_with_no_perms):
        # 4. Prepare data for process creation
        department = await create_test_department_async(async_db_session, organization_id=org_id, name=f"RBAC Dept NoPerms {uuid.uuid4().hex[:6]}")
        process_payload = _get_base_process_payload(department.id, user_with_no_perms.id)

        # 5. Action: Attempt to create a process
        response = await authed_client.post("/api/v1/processes/", json=process_payload)

        # 6. Assert: Expect 403 Forbidden
        assert response.status_code == 403, response.text
        response_data = response.json()
        assert "do not have the required permission" in response_data["detail"].lower()
        assert ProcessPermissions.CREATE in response_data["detail"]


@pytest.mark.asyncio
async def test_create_process_duplicate_name_in_department(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: Create a role with 'process:create' permission
    creator_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"ProcessCreatorRole_DupTest_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE], organization_id=org_id
    )

    # 2. Setup: Create a user with this role
    user_with_create_perm = await create_user_with_roles_async(
        db_session=async_db_session, email=f"creator_duptest_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[creator_role.name], organization_id=org_id
    )

    # 3. Get client for this user
    async for authed_client in async_client_authenticated_as_user_factory(user_with_create_perm):
        # 4. Prepare data for process creation
        department = await create_test_department_async(async_db_session, organization_id=org_id, name=f"RBAC Dept DupTest {uuid.uuid4().hex[:6]}")
        process_name = f"Duplicate Test Process {uuid.uuid4().hex[:6]}"
        process_payload_1 = ProcessCreate(
            name=process_name,
            description="Initial process for duplicate name testing.",
            department_id=department.id,
            process_owner_id=user_with_create_perm.id,
            rto=1.0, rpo=1.0, criticality_level="Low"
        ).model_dump(mode='json')

        # 5. Action: Create the first process successfully
        response1 = await authed_client.post("/api/v1/processes/", json=process_payload_1)
        assert response1.status_code == 201, f"Failed to create initial process: {response1.text}"

        # 6. Prepare payload for the second process with the same name and department
        process_payload_2 = ProcessCreate(
            name=process_name, # Same name
            description="Attempt to create duplicate process.",
            department_id=department.id, # Same department
            process_owner_id=user_with_create_perm.id,
            rto=2.0, rpo=2.0, criticality_level="Medium"
        ).model_dump(mode='json')

        # 7. Action: Attempt to create the second process (duplicate)
        response2 = await authed_client.post("/api/v1/processes/", json=process_payload_2)

        # 8. Assert: Expect 400 Bad Request
        assert response2.status_code == 400, response2.text
        response_data = response2.json()
        assert "detail" in response_data
        expected_error_message = f"A process with the name '{process_name}' already exists in the department '{department.name}'."
        assert response_data["detail"] == expected_error_message


@pytest.mark.asyncio
async def test_create_process_with_location_from_different_organization(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel # User from the "main" org (org1)
):
    org1_id = async_default_app_user.organization_id
    assert org1_id is not None

    # 1. Setup: User in org1 with 'process:create' permission
    creator_role_org1 = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"ProcCreatorLocXOrg_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE], organization_id=org1_id
    )
    user_in_org1 = await create_user_with_roles_async(
        db_session=async_db_session, email=f"creator_loc_x_org_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[creator_role_org1.name], organization_id=org1_id
    )
    # Refresh user before creating client to ensure permissions are loaded
    await async_db_session.refresh(user_in_org1, attribute_names=['roles'])
    for role in user_in_org1.roles:
        await async_db_session.refresh(role, attribute_names=['permissions'])
    async for authed_client_org1 in async_client_authenticated_as_user_factory(user_in_org1):
        # 2. Setup: Department in org1
        department_org1 = await create_test_department_async(
            async_db_session, organization_id=org1_id, name=f"DeptForProcLocXOrg {uuid.uuid4().hex[:6]}"
        )

        # 3. Setup: Create "other" organization (org2)
        org2_id = uuid.uuid4()
        org2 = OrganizationModel(id=org2_id, name=f"Other Org For Location Test {uuid.uuid4().hex[:4]}", industry="Testing")
        async_db_session.add(org2)

        # 4. Setup: Location in org2
        location_in_org2 = LocationModel(
            id=uuid.uuid4(),
            name=f"Location in Org2 {uuid.uuid4().hex[:6]}",
            organization_id=org2_id, # Belongs to org2
            address_line1="123 Other St", # Corrected attribute name
            city="Otherville",
            country="OT"
            # created_by_id and updated_by_id are not in the current LocationModel definition
        )
        async_db_session.add(location_in_org2)
        await async_db_session.commit() # Commit org2 and location_in_org2

        # 5. Prepare payload: Attempt to create process in department_org1 (org1)
        # but link to location_in_org2
        process_payload = ProcessCreate(
            name=f"Process X-Org Location {uuid.uuid4().hex[:6]}",
            description="Testing cross-org location linking.",
            department_id=department_org1.id,
            process_owner_id=user_in_org1.id,
            rto=1.0, rpo=1.0, criticality_level="Low",
            location_ids=[location_in_org2.id] # Location from org2
        ).model_dump(mode='json')

        # 6. Action: Attempt to create the process
        response = await authed_client_org1.post("/api/v1/processes/", json=process_payload)

        # 7. Assert: Expect 400 Bad Request (due to cross-organization linking)
        assert response.status_code == 400, response.text
        response_data = response.json()
        assert "detail" in response_data
        assert "location" in response_data["detail"].lower()
        assert "different organization" in response_data["detail"].lower()


@pytest.mark.asyncio
async def test_create_process_with_invalid_department_id(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: User with 'process:create' permission
    creator_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"ProcCreatorInvalidDept_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE], organization_id=org_id
    )
    user_with_create_perm = await create_user_with_roles_async(
        db_session=async_db_session, email=f"creator_invalid_dept_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[creator_role.name], organization_id=org_id
    )
    # Refresh user before creating client
    await async_db_session.refresh(user_with_create_perm, attribute_names=['roles'])
    for role in user_with_create_perm.roles:
        await async_db_session.refresh(role, attribute_names=['permissions'])
    async for authed_client in async_client_authenticated_as_user_factory(user_with_create_perm):
        # 2. Prepare payload with a non-existent department_id
        non_existent_dept_id = uuid.uuid4()
        process_payload = ProcessCreate(
            name=f"Process Invalid Dept {uuid.uuid4().hex[:6]}",
            description="Testing invalid department.",
            department_id=non_existent_dept_id, # Invalid department ID
            rto=1.0, rpo=1.0, criticality_level="Low"
        ).model_dump(mode='json')

        # 3. Action: Attempt to create the process
        response = await authed_client.post("/api/v1/processes/", json=process_payload)

        # 4. Assert: Expect 404 Not Found (due to _get_department_if_valid)
        assert response.status_code == 404, response.text
        response_data = response.json()
        assert "detail" in response_data
        assert f"Department with ID {non_existent_dept_id} not found in your organization or has been deleted." in response_data["detail"]


@pytest.mark.asyncio
async def test_create_process_with_invalid_owner_id(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: User with 'process:create' permission
    creator_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"ProcCreatorInvalidOwner_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE], organization_id=org_id
    )
    user_with_create_perm = await create_user_with_roles_async(
        db_session=async_db_session, email=f"creator_invalid_owner_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[creator_role.name], organization_id=org_id
    )
    await async_db_session.refresh(user_with_create_perm, attribute_names=['roles'])
    for role in user_with_create_perm.roles:
        await async_db_session.refresh(role, attribute_names=['permissions'])
    async for authed_client in async_client_authenticated_as_user_factory(user_with_create_perm):
        # 2. Setup: Valid department in the organization
        department = await create_test_department_async(async_db_session, organization_id=org_id, name=f"DeptForInvalidOwnerTest {uuid.uuid4().hex[:6]}")

        # 3. Prepare payload with a non-existent process_owner_id
        non_existent_owner_id = uuid.uuid4()
        process_payload = ProcessCreate(
            name=f"Process Invalid Owner {uuid.uuid4().hex[:6]}",
            description="Testing invalid process owner.",
            department_id=department.id,
            process_owner_id=non_existent_owner_id, # Invalid owner ID
            rto=1.0, rpo=1.0, criticality_level="Low"
        ).model_dump(mode='json')

        # 4. Action: Attempt to create the process
        response = await authed_client.post("/api/v1/processes/", json=process_payload)

        # 5. Assert: Expect 404 Not Found (due to _get_user_if_valid in ProcessService)
        assert response.status_code == 404, response.text
        response_data = response.json()
        assert "detail" in response_data
        assert f"User with ID {non_existent_owner_id} not found in your organization or is inactive." in response_data["detail"]


@pytest.mark.asyncio
async def test_create_process_with_invalid_application_ids(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel,
    default_department_async: DepartmentModel,
    default_application_async: ApplicationModel # Assuming a fixture for a valid application
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: User with 'process:create' permission
    creator_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"ProcCreatorInvalidApp_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE], organization_id=org_id
    )
    user_with_create_perm = await create_user_with_roles_async(
        db_session=async_db_session, email=f"creator_invalid_app_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[creator_role.name], organization_id=org_id
    )
    await async_db_session.refresh(user_with_create_perm, attribute_names=['roles'])
    for role in user_with_create_perm.roles:
        await async_db_session.refresh(role, attribute_names=['permissions'])
    async for authed_client in async_client_authenticated_as_user_factory(user_with_create_perm):
        # Ensure default department and application are in the same org as the user
        assert default_department_async.organization_id == org_id
        assert default_application_async.organization_id == org_id

        # 2. Prepare payload with one valid and one non-existent application_id
        non_existent_app_id = uuid.uuid4()
        invalid_application_ids = [default_application_async.id, non_existent_app_id]

        process_payload = ProcessCreate(
            name=f"Process Invalid App {uuid.uuid4().hex[:6]}",
            description="Testing invalid application IDs.",
            department_id=default_department_async.id,
            application_ids=invalid_application_ids,
            rto=1.0, rpo=1.0, criticality_level="Low"
        ).model_dump(mode='json')

        # 3. Action: Attempt to create the process
        response = await authed_client.post("/api/v1/processes/", json=process_payload)

        # 4. Assert: Expect 404 Not Found
        assert response.status_code == 404, response.text
        response_data = response.json()
        assert "detail" in response_data
        # The error message will contain the set of missing IDs
        expected_missing_ids_str = str({non_existent_app_id}) # Convert set to string for comparison
        assert f"One or more applications not found or not in your organization: {expected_missing_ids_str}" in response_data["detail"]


@pytest.mark.asyncio
async def test_create_process_with_invalid_upstream_dependency_ids(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel,
    default_department_async: DepartmentModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: User with 'process:create' permission
    creator_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"ProcCreatorInvalidUpstream_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE], organization_id=org_id
    )
    user_with_create_perm = await create_user_with_roles_async(
        db_session=async_db_session, email=f"creator_invalid_upstream_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[creator_role.name], organization_id=org_id
    )
    await async_db_session.refresh(user_with_create_perm, attribute_names=['roles'])
    for role in user_with_create_perm.roles:
        await async_db_session.refresh(role, attribute_names=['permissions'])
    async for authed_client in async_client_authenticated_as_user_factory(user_with_create_perm):
        assert default_department_async.organization_id == org_id

        # 2. Prepare payload with a non-existent upstream_dependency_id
        non_existent_process_id = uuid.uuid4()
        invalid_upstream_ids = [non_existent_process_id]

        process_payload = ProcessCreate(
            name=f"Process Invalid Upstream {uuid.uuid4().hex[:6]}",
            description="Testing invalid upstream dependency IDs.",
            department_id=default_department_async.id,
            upstream_dependency_ids=invalid_upstream_ids,
            rto=1.0, rpo=1.0, criticality_level="Low"
        ).model_dump(mode='json')

        # 3. Action: Attempt to create the process
        response = await authed_client.post("/api/v1/processes/", json=process_payload)

        # 4. Assert: Expect 404 Not Found
        assert response.status_code == 404, response.text
        response_data = response.json()
        assert "detail" in response_data
        expected_missing_ids_str = str({non_existent_process_id})
        assert f"One or more dependent processes not found or not in your organization: {expected_missing_ids_str}" in response_data["detail"]


@pytest.mark.asyncio
async def test_create_process_with_invalid_downstream_dependency_ids(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel,
    default_department_async: DepartmentModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: User with 'process:create' permission
    creator_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"ProcCreatorInvalidDownstream_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE], organization_id=org_id
    )
    user_with_create_perm = await create_user_with_roles_async(
        db_session=async_db_session, email=f"creator_invalid_downstream_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[creator_role.name], organization_id=org_id
    )
    await async_db_session.refresh(user_with_create_perm, attribute_names=['roles'])
    for role in user_with_create_perm.roles:
        await async_db_session.refresh(role, attribute_names=['permissions'])
    async for authed_client in async_client_authenticated_as_user_factory(user_with_create_perm):
        assert default_department_async.organization_id == org_id

        # 2. Prepare payload with a non-existent downstream_dependency_id
        non_existent_process_id = uuid.uuid4()
        invalid_downstream_ids = [non_existent_process_id]

        process_payload = ProcessCreate(
            name=f"Process Invalid Downstream {uuid.uuid4().hex[:6]}",
            description="Testing invalid downstream dependency IDs.",
            department_id=default_department_async.id,
            downstream_dependency_ids=invalid_downstream_ids,
            rto=1.0, rpo=1.0, criticality_level="Low"
        ).model_dump(mode='json')

        # 3. Action: Attempt to create the process
        response = await authed_client.post("/api/v1/processes/", json=process_payload)

        # 4. Assert: Expect 404 Not Found
        assert response.status_code == 404, response.text
        response_data = response.json()
        assert "detail" in response_data
        expected_missing_ids_str = str({non_existent_process_id})
        assert f"One or more dependent processes not found or not in your organization: {expected_missing_ids_str}" in response_data["detail"]


# Helper to create a process for RBAC testing (assumes user has create permission)
async def _create_test_process_for_rbac(
    client: AsyncClient,
    async_db_session: AsyncSession,
    org_id: uuid.UUID,
    user_id_for_owner: Optional[uuid.UUID] = None
) -> ProcessModel:
    department = await create_test_department_async(async_db_session, organization_id=org_id, name=f"RBAC Dept Read Test {uuid.uuid4().hex[:6]}")
    process_payload = _get_base_process_payload(department.id, owner_id=user_id_for_owner)

    response = await client.post("/api/v1/processes/", json=process_payload)
    assert response.status_code == 201, f"Failed to create test process for RBAC read tests: {response.text}"
    response_data = response.json()

    process = await async_db_session.get(ProcessModel, uuid.UUID(response_data["id"]))
    assert process is not None, "Created process not found in DB"
    return process

# --- RBAC Test Cases for GET /processes/{process_id} (Read Process) ---

@pytest.mark.asyncio
async def test_rbac_read_process_with_permission(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: User with create+read permissions to create and then read a process
    creator_reader_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"ProcCreatorReader_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE, ProcessPermissions.READ], organization_id=org_id
    )
    test_user = await create_user_with_roles_async(
        db_session=async_db_session, email=f"cr_reader_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[creator_reader_role.name], organization_id=org_id
    )
    async for authed_client in async_client_authenticated_as_user_factory(test_user):
        # 2. Create a process to be read
        process_to_read = await _create_test_process_for_rbac(authed_client, async_db_session, org_id, test_user.id)

        # 3. Action: Attempt to read the process with the same user (who has read permission)
        response = await authed_client.get(f"/api/v1/processes/{process_to_read.id}")

        # 4. Assert: Expect success (200 OK)
        assert response.status_code == 200, response.text
        response_data = response.json()
        assert response_data["id"] == str(process_to_read.id)
        assert response_data["name"] == process_to_read.name

@pytest.mark.asyncio
async def test_rbac_read_process_without_read_permission(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: User with only CREATE permission (to create the process)
    creator_only_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"ProcCreatorOnly_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE], organization_id=org_id
    )
    creator_user = await create_user_with_roles_async(
        db_session=async_db_session, email=f"creator_only_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[creator_only_role.name], organization_id=org_id
    )
    async for creator_client in async_client_authenticated_as_user_factory(creator_user):
        # 2. Create a process with the creator_user
        process_to_read = await _create_test_process_for_rbac(creator_client, async_db_session, org_id, creator_user.id)

        # 3. Setup: User with some other permission (e.g., UPDATE) but NOT READ
        updater_only_role = await create_role_with_permissions_async(
            db_session=async_db_session, role_name=f"ProcUpdaterOnly_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.UPDATE], organization_id=org_id
        )
        user_without_read_perm = await create_user_with_roles_async(
            db_session=async_db_session, email=f"updater_no_read_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[updater_only_role.name], organization_id=org_id
        )
        async for reader_client in async_client_authenticated_as_user_factory(user_without_read_perm):
            # 4. Action: Attempt to read the process with user_without_read_perm
            response = await reader_client.get(f"/api/v1/processes/{process_to_read.id}")

            # 5. Assert: Expect 403 Forbidden
            assert response.status_code == 403, response.text
            response_data = response.json()
            assert "do not have the required permission" in response_data["detail"].lower()
            assert ProcessPermissions.READ in response_data["detail"]

@pytest.mark.asyncio
async def test_rbac_read_process_with_no_relevant_permissions(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: User with CREATE permission to create the process
    creator_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"ProcCreatorForNoPermRead_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE], organization_id=org_id
    )
    creator_user = await create_user_with_roles_async(
        db_session=async_db_session, email=f"creator_for_noperm_read_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[creator_role.name], organization_id=org_id
    )
    async for creator_client in async_client_authenticated_as_user_factory(creator_user):
        # 2. Create a process
        process_to_read = await _create_test_process_for_rbac(creator_client, async_db_session, org_id, creator_user.id)

        # 3. Setup: User with a role that has no process-related permissions
        no_process_perms_role = await create_role_with_permissions_async(
            db_session=async_db_session, role_name=f"NoProcPermsReadRole_{uuid.uuid4().hex[:4]}", permissions_names=["dummy:other_permission_read_test"], organization_id=org_id
        )
        user_with_no_relevant_perms = await create_user_with_roles_async(
            db_session=async_db_session, email=f"noperms_reader_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[no_process_perms_role.name], organization_id=org_id
        )
        async for reader_client in async_client_authenticated_as_user_factory(user_with_no_relevant_perms):
            # 4. Action: Attempt to read the process
            response = await reader_client.get(f"/api/v1/processes/{process_to_read.id}")

            # 5. Assert: Expect 403 Forbidden
            assert response.status_code == 403, response.text
            response_data = response.json()
            assert "do not have the required permission" in response_data["detail"].lower()
            assert ProcessPermissions.READ in response_data["detail"]

@pytest.mark.asyncio
async def test_rbac_read_process_from_different_organization(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel # User from the "main" org
):
    main_org_id = async_default_app_user.organization_id
    assert main_org_id is not None

    # 1. Setup: Create a user and client for the main organization with CREATE+READ perms
    main_org_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"MainOrgProcCR_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE, ProcessPermissions.READ], organization_id=main_org_id
    )
    main_org_user_for_reading = await create_user_with_roles_async(
        db_session=async_db_session, email=f"main_org_cr_user_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[main_org_role.name], organization_id=main_org_id
    )
    async for main_org_reader_client in async_client_authenticated_as_user_factory(main_org_user_for_reading):
        # 2. Setup: Create a "different" organization
        other_org = OrganizationModel(id=uuid.uuid4(), name=f"Other Org For Read Test {uuid.uuid4().hex[:4]}", industry="Testing")
        async_db_session.add(other_org)
        await async_db_session.flush() # Ensure other_org.id is available

        # 3. Setup: Create a user in the "different" organization with CREATE permission
        other_org_creator_role = await create_role_with_permissions_async(
            db_session=async_db_session, role_name=f"OtherOrgProcCreator_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE], organization_id=other_org.id
        )
        other_org_creator_user = await create_user_with_roles_async(
            db_session=async_db_session, email=f"other_org_creator_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[other_org_creator_role.name], organization_id=other_org.id
        )
        async for other_org_creator_client in async_client_authenticated_as_user_factory(other_org_creator_user):
            # 4. Create a process in the "different" organization using its own user/client
            process_in_other_org = await _create_test_process_for_rbac(other_org_creator_client, async_db_session, other_org.id, other_org_creator_user.id)
            await async_db_session.commit() # Commit everything created so far, especially the new process

            # 5. Action: Attempt to read the process from the "different" organization
            # using the client authenticated for the "main" organization user (main_org_reader_client from outer loop)
            response = await main_org_reader_client.get(f"/api/v1/processes/{process_in_other_org.id}")

            # 6. Assert: Expect 403 Forbidden
            assert response.status_code == 403, response.text
            response_data = response.json()
            assert "do not have the required permission" in response_data["detail"].lower()


# --- RBAC Test Cases for PUT /processes/{process_id} (Update Process) ---

@pytest.mark.asyncio
async def test_rbac_update_process_with_permission(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: User with create + update permissions
    creator_updater_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"ProcCreatorUpdater_{uuid.uuid4().hex[:4]}", 
        permissions_names=[ProcessPermissions.CREATE, ProcessPermissions.UPDATE], 
        organization_id=org_id
    )
    test_user = await create_user_with_roles_async(
        db_session=async_db_session, email=f"creator_updater_{uuid.uuid4().hex[:6]}@example.com", 
        first_name="TestFirstName", last_name="TestLastName", 
        role_names=[creator_updater_role.name], 
        organization_id=org_id
    )
    async for authed_client in async_client_authenticated_as_user_factory(test_user):
        # 2. Create a process to be updated
        process_to_update = await _create_test_process_for_rbac(authed_client, async_db_session, org_id, test_user.id)

        # 3. Prepare update data
        update_payload = {"name": f"Updated Process Name {uuid.uuid4().hex[:6]}", "description": "Updated description."}

        # 4. Action: Attempt to update the process
        response = await authed_client.put(f"/api/v1/processes/{process_to_update.id}", json=update_payload)

        # 5. Assert: Expect success (200 OK)
        assert response.status_code == 200, response.text
        response_data = response.json()
        assert response_data["id"] == str(process_to_update.id)
        assert response_data["name"] == update_payload["name"]
        assert response_data["description"] == update_payload["description"]

        # Verify in DB
        await async_db_session.refresh(process_to_update) # Refresh to get latest state
        assert process_to_update.name == update_payload["name"]

@pytest.mark.asyncio
async def test_rbac_update_process_without_update_permission(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: User with CREATE permission (to create the process)
    creator_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"ProcCreatorForUpdateTest_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE], organization_id=org_id
    )
    creator_user = await create_user_with_roles_async(
        db_session=async_db_session, email=f"creator_for_update_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[creator_role.name], organization_id=org_id
    )
    async for creator_client in async_client_authenticated_as_user_factory(creator_user):
        # 2. Create a process
        process_to_update = await _create_test_process_for_rbac(creator_client, async_db_session, org_id, creator_user.id)

        # 3. Setup: User with a different permission (e.g., READ) but NOT UPDATE
        reader_role = await create_role_with_permissions_async(
            db_session=async_db_session, role_name=f"ProcReaderForUpdateTest_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.READ], organization_id=org_id
        )
        user_without_update_perm = await create_user_with_roles_async(
            db_session=async_db_session, email=f"reader_no_update_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[reader_role.name], organization_id=org_id
        )
        async for updater_client in async_client_authenticated_as_user_factory(user_without_update_perm):
            update_payload = {"name": "Attempted Update"}

            # 4. Action: Attempt to update the process
            response = await updater_client.put(f"/api/v1/processes/{process_to_update.id}", json=update_payload)

            # 5. Assert: Expect 403 Forbidden
            assert response.status_code == 403, response.text
            response_data = response.json()
            assert "do not have the required permission" in response_data["detail"].lower()
            assert ProcessPermissions.UPDATE in response_data["detail"]

@pytest.mark.asyncio
async def test_rbac_update_process_with_no_relevant_permissions(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: User with CREATE permission to create the process
    creator_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"ProcCreatorForNoPermUpdate_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE], organization_id=org_id
    )
    creator_user = await create_user_with_roles_async(
        db_session=async_db_session, email=f"creator_for_noperm_update_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[creator_role.name], organization_id=org_id
    )
    async for creator_client in async_client_authenticated_as_user_factory(creator_user):
        # 2. Create a process
        process_to_update = await _create_test_process_for_rbac(creator_client, async_db_session, org_id, creator_user.id)

        # 3. Setup: User with a role that has no process-related permissions
        no_process_perms_role = await create_role_with_permissions_async(
            db_session=async_db_session, role_name=f"NoProcPermsUpdateRole_{uuid.uuid4().hex[:4]}", permissions_names=["dummy:other_permission_update_test"], organization_id=org_id
        )
        user_with_no_relevant_perms = await create_user_with_roles_async(
            db_session=async_db_session, email=f"noperms_updater_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[no_process_perms_role.name], organization_id=org_id
        )
        async for updater_client in async_client_authenticated_as_user_factory(user_with_no_relevant_perms):
            update_payload = {"name": "Attempted Update NoPerms"}

            # 4. Action: Attempt to update the process
            response = await updater_client.put(f"/api/v1/processes/{process_to_update.id}", json=update_payload)

            # 5. Assert: Expect 403 Forbidden
            assert response.status_code == 403, response.text
            response_data = response.json()
            assert "do not have the required permission" in response_data["detail"].lower()
            assert ProcessPermissions.UPDATE in response_data["detail"]

@pytest.mark.asyncio
async def test_rbac_update_process_from_different_organization(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel # User from the "main" org
):
    main_org_id = async_default_app_user.organization_id
    assert main_org_id is not None

    # 1. Setup: User and client for the main organization with UPDATE permission
    main_org_updater_role = await create_role_with_permissions_async(
        db_session=async_db_session, role_name=f"MainOrgProcUpdater_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.UPDATE], organization_id=main_org_id
    )
    main_org_user_for_updating = await create_user_with_roles_async(
        db_session=async_db_session, email=f"main_org_updater_user_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[main_org_updater_role.name], organization_id=main_org_id
    )
    async for main_org_updater_client in async_client_authenticated_as_user_factory(main_org_user_for_updating):
        # 2. Setup: Create a "different" organization
        other_org = OrganizationModel(id=uuid.uuid4(), name=f"Other Org For Update Test {uuid.uuid4().hex[:4]}", industry="Testing")
        async_db_session.add(other_org)
        await async_db_session.flush()

        # 3. Setup: User in "different" org with CREATE permission (to create the target process)
        other_org_creator_role = await create_role_with_permissions_async(
            db_session=async_db_session, role_name=f"OtherOrgProcCreatorForUpdate_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE], organization_id=other_org.id
        )
        other_org_creator_user = await create_user_with_roles_async(
            db_session=async_db_session, email=f"other_org_creator_for_update_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", role_names=[other_org_creator_role.name], organization_id=other_org.id
        )
        process_in_other_org = None # Initialize to ensure it's defined in the outer scope
        async for other_org_creator_client in async_client_authenticated_as_user_factory(other_org_creator_user):
            # 4. Create a process in the "different" organization
            process_in_other_org = await _create_test_process_for_rbac(other_org_creator_client, async_db_session, other_org.id, other_org_creator_user.id)
            await async_db_session.commit() # Commit inside inner loop
            # Assuming the factory yields only one client, this inner loop runs once.
            # If it could yield multiple, process_in_other_org would be overwritten.
            # For this test, we expect one process to be created.

        # Ensure the process was created before attempting to use it
        assert process_in_other_org is not None, "Process was not created in the 'other' organization."

        update_payload = {"name": "Attempted Cross-Org Update"}

        # 5. Action: Attempt to update the process in "different" org using client from "main" org
        response = await main_org_updater_client.put(f"/api/v1/processes/{process_in_other_org.id}", json=update_payload)

        # 6. Assert: Expect 403 Forbidden
        assert response.status_code == 403, response.text
        response_data = response.json()
        assert "do not have the required permission" in response_data["detail"].lower()


@pytest.mark.asyncio
async def test_update_process_name_to_duplicate_in_same_department(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: Role with create and update permissions for processes
    process_manager_role = await create_role_with_permissions_async(
        db_session=async_db_session, 
        role_name=f"ProcessManagerDuplicateTestRole_{uuid.uuid4().hex[:4]}", 
        permissions_names=[ProcessPermissions.CREATE, ProcessPermissions.UPDATE, ProcessPermissions.READ], 
        organization_id=org_id
    )
    process_manager_user = await create_user_with_roles_async(
        db_session=async_db_session, 
        email=f"procmanager_dup_{uuid.uuid4().hex[:6]}@example.com", 
        first_name="TestFirstName", last_name="TestLastName", 
        role_names=[process_manager_role.name], 
        organization_id=org_id
    )
    async for authed_client in async_client_authenticated_as_user_factory(process_manager_user):
        # 2. Create a department
        department = await create_test_department_async(async_db_session, organization_id=org_id, name=f"DeptForDuplicateUpdateTest_{uuid.uuid4().hex[:6]}")

        # 3. Create initial process "Process Alpha"
        process_alpha_name = f"Process Alpha {uuid.uuid4().hex[:6]}"
        process_alpha_payload = _get_base_process_payload(department.id, process_manager_user.id)
        process_alpha_payload["name"] = process_alpha_name
        
        response_alpha = await authed_client.post("/api/v1/processes/", json=process_alpha_payload)
        assert response_alpha.status_code == 201, response_alpha.text
        process_alpha_id = response_alpha.json()["id"]

        # 4. Create second process "Process Beta"
        process_beta_payload = _get_base_process_payload(department.id, process_manager_user.id)
        process_beta_payload["name"] = f"Process Beta {uuid.uuid4().hex[:6]}"

        response_beta = await authed_client.post("/api/v1/processes/", json=process_beta_payload)
        assert response_beta.status_code == 201, response_beta.text
        process_beta_id = response_beta.json()["id"]

        # 5. Attempt to update "Process Beta" to have the name "Process Alpha"
        update_payload = ProcessUpdate(name=process_alpha_name).model_dump(mode='json', exclude_unset=True)

        response_update = await authed_client.put(f"/api/v1/processes/{process_beta_id}", json=update_payload)

        # 6. Assert: Expect 409 Conflict
        assert response_update.status_code == 409, response_update.text
        response_data = response_update.json()
        assert "already exists in the department" in response_data["detail"]
        assert process_alpha_name in response_data["detail"]

        # Verify Process Beta still has its original name in DB (or is unchanged)
        process_beta_db = await async_db_session.get(ProcessModel, uuid.UUID(process_beta_id))
        assert process_beta_db is not None
        assert process_beta_db.name == process_beta_payload["name"]


@pytest.mark.asyncio
async def test_update_process_department_to_different_organization(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel # User from the "main" org (org1)
):
    org1_id = async_default_app_user.organization_id
    assert org1_id is not None

    # 1. Setup: User with update permission in org1
    updater_role_org1 = await create_role_with_permissions_async(db_session=async_db_session, role_name=f"UpdaterRoleOrg1_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE, ProcessPermissions.UPDATE, ProcessPermissions.READ], organization_id=org1_id)
    updater_user_org1 = await create_user_with_roles_async(db_session=async_db_session, email=f"updater_org1_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org1_id, role_names=[updater_role_org1.name])
    async for authed_client_org1 in async_client_authenticated_as_user_factory(updater_user_org1):
        # 2. Create a department in org1
        dept_org1 = await create_test_department_async(async_db_session, organization_id=org1_id, name=f"DeptOrg1Update_{uuid.uuid4().hex[:6]}")
        
        # 3. Create a process in org1
        process_payload_org1 = _get_base_process_payload(department_id=dept_org1.id, owner_id=updater_user_org1.id)
        response_create = await authed_client_org1.post("/api/v1/processes/", json=process_payload_org1)
        assert response_create.status_code == 201, response_create.text
        process_to_update_id = response_create.json()["id"]

        # 4. Create a different organization (org2) and a department in it
        org2 = await create_test_organization_async(async_db_session, name="Org2ForProcessUpdateTest")
        dept_org2 = await create_test_department_async(async_db_session, organization_id=org2.id, name=f"DeptOrg2_{uuid.uuid4().hex[:6]}")

        # 5. Attempt to update the process in org1 to use dept_org2
        update_payload = ProcessUpdate(department_id=dept_org2.id).model_dump(mode='json', exclude_unset=True)
        response_update = await authed_client_org1.put(f"/api/v1/processes/{process_to_update_id}", json=update_payload)

        # 6. Assert: Expect 404 Not Found (as _get_department_if_valid won't find dept_org2 in org1)
        assert response_update.status_code == 404, response_update.text
        assert f"Department with ID {dept_org2.id} not found" in response_update.json()["detail"]

@pytest.mark.asyncio
async def test_update_process_owner_to_different_organization(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org1_id = async_default_app_user.organization_id
    assert org1_id is not None

    updater_role_org1 = await create_role_with_permissions_async(db_session=async_db_session, role_name=f"UpdOwnRoleOrg1_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE, ProcessPermissions.UPDATE, ProcessPermissions.READ], organization_id=org1_id)
    updater_user_org1 = await create_user_with_roles_async(db_session=async_db_session, email=f"updowner_org1_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org1_id, role_names=[updater_role_org1.name])
    async for authed_client_org1 in async_client_authenticated_as_user_factory(updater_user_org1):
        dept_org1 = await create_test_department_async(async_db_session, organization_id=org1_id, name=f"DeptOwnUpdate_{uuid.uuid4().hex[:6]}")
        process_payload_org1 = _get_base_process_payload(department_id=dept_org1.id, owner_id=updater_user_org1.id)
        response_create = await authed_client_org1.post("/api/v1/processes/", json=process_payload_org1)
        assert response_create.status_code == 201, response_create.text
        process_to_update_id = response_create.json()["id"]

        org2 = await create_test_organization_async(async_db_session, name="Org2ForOwnerUpdateTest")
        # Create a user in org2 to be the invalid owner
        user_in_org2 = await create_user_with_roles_async(db_session=async_db_session, email=f"user_org2_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org2.id, role_names=[]) # No specific role needed for this test user

        update_payload = ProcessUpdate(process_owner_id=user_in_org2.id).model_dump(mode='json', exclude_unset=True)
        response_update = await authed_client_org1.put(f"/api/v1/processes/{process_to_update_id}", json=update_payload)

        assert response_update.status_code == 404, response_update.text
        assert f"User with ID {user_in_org2.id} not found" in response_update.json()["detail"]

@pytest.mark.asyncio
async def test_update_process_location_from_different_organization(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel,
    default_location_async: LocationModel # Location in org1
):
    org1_id = async_default_app_user.organization_id
    assert org1_id is not None
    assert default_location_async.organization_id == org1_id

    updater_role_org1 = await create_role_with_permissions_async(db_session=async_db_session, role_name=f"UpdLocRoleOrg1_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE, ProcessPermissions.UPDATE, ProcessPermissions.READ], organization_id=org1_id)
    updater_user_org1 = await create_user_with_roles_async(db_session=async_db_session, email=f"updloc_org1_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org1_id, role_names=[updater_role_org1.name])
    async for authed_client_org1 in async_client_authenticated_as_user_factory(updater_user_org1):
        dept_org1 = await create_test_department_async(async_db_session, organization_id=org1_id, name=f"DeptLocUpdate_{uuid.uuid4().hex[:6]}")
        
        # 1. Create process with an initial location
        process_payload = _get_base_process_payload(department_id=dept_org1.id, owner_id=updater_user_org1.id, location_ids=[default_location_async.id])
        response_create = await authed_client_org1.post("/api/v1/processes/", json=process_payload)
        assert response_create.status_code == 201, response_create.text
        process_to_update_id = response_create.json()["id"]

        org2 = await create_test_organization_async(async_db_session, name="Org2ForLocUpdateTest")
        location_org2 = await create_test_location_async(async_db_session, organization_id=org2.id, name="LocationInOrg2")

        update_payload = ProcessUpdate(location_ids=[location_org2.id]).model_dump(mode='json', exclude_unset=True)
        response_update = await authed_client_org1.put(f"/api/v1/processes/{process_to_update_id}", json=update_payload)

        assert response_update.status_code == 404, response_update.text # _get_valid_locations raises 404
        assert "One or more locations not found" in response_update.json()["detail"]
        assert str(location_org2.id) in response_update.json()["detail"]

@pytest.mark.asyncio
async def test_update_process_application_from_different_organization(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel,
    default_application_async: ApplicationModel # Application in org1
):
    org1_id = async_default_app_user.organization_id
    assert org1_id is not None
    assert default_application_async.organization_id == org1_id

    updater_role_org1 = await create_role_with_permissions_async(db_session=async_db_session, role_name=f"UpdAppRoleOrg1_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE, ProcessPermissions.UPDATE, ProcessPermissions.READ], organization_id=org1_id)
    updater_user_org1 = await create_user_with_roles_async(db_session=async_db_session, email=f"updapp_org1_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org1_id, role_names=[updater_role_org1.name])
    async for authed_client_org1 in async_client_authenticated_as_user_factory(updater_user_org1):
        dept_org1 = await create_test_department_async(async_db_session, organization_id=org1_id, name=f"DeptAppUpdate_{uuid.uuid4().hex[:6]}")
        process_payload_org1 = _get_base_process_payload(department_id=dept_org1.id, owner_id=updater_user_org1.id, application_ids=[default_application_async.id])
        response_create = await authed_client_org1.post("/api/v1/processes/", json=process_payload_org1)
        assert response_create.status_code == 201, response_create.text
        process_to_update_id = response_create.json()["id"]

        org2 = await create_test_organization_async(async_db_session, name="Org2ForAppUpdateTest")
        app_org2 = await create_test_application_async(async_db_session, organization_id=org2.id, name="AppInOrg2")

        update_payload = ProcessUpdate(application_ids=[app_org2.id]).model_dump(mode='json', exclude_unset=True)
        response_update = await authed_client_org1.put(f"/api/v1/processes/{process_to_update_id}", json=update_payload)

        assert response_update.status_code == 404, response_update.text # _get_valid_applications raises 404
        assert "One or more applications not found" in response_update.json()["detail"]
        assert str(app_org2.id) in response_update.json()["detail"]

@pytest.mark.asyncio
async def test_update_process_dependency_from_different_organization(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org1_id = async_default_app_user.organization_id
    assert org1_id is not None

    updater_role_org1 = await create_role_with_permissions_async(db_session=async_db_session, role_name=f"UpdDepRoleOrg1_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE, ProcessPermissions.UPDATE, ProcessPermissions.READ], organization_id=org1_id)
    updater_user_org1 = await create_user_with_roles_async(db_session=async_db_session, email=f"upddep_org1_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org1_id, role_names=[updater_role_org1.name])
    # Create a different organization (org2) and a process in it to be the invalid dependency
    org2 = await create_test_organization_async(async_db_session, name="Org2ForDepUpdateTest")
    dept_org2 = await create_test_department_async(async_db_session, organization_id=org2.id, name=f"DeptInOrg2_{uuid.uuid4().hex[:6]}")
    # Need a user in org2 to be owner for process creation in org2
    user_org2_owner = await create_user_with_roles_async(db_session=async_db_session, email=f"owner_org2_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org2.id, role_names=[])
    # Let's create it directly for test setup simplicity.
    process_in_org2 = ProcessModel(name=f"ProcessInOrg2_{uuid.uuid4().hex[:6]}", department_id=dept_org2.id, organization_id=org2.id, created_by_id=user_org2_owner.id)
    async_db_session.add(process_in_org2)
    await async_db_session.commit()
    await async_db_session.refresh(process_in_org2)

    async for authed_client_org1 in async_client_authenticated_as_user_factory(updater_user_org1):
        dept_org1 = await create_test_department_async(async_db_session, organization_id=org1_id, name=f"DeptDepUpdate_{uuid.uuid4().hex[:6]}")
        
        # Create process to be updated in org1
        process_to_update_payload = _get_base_process_payload(department_id=dept_org1.id, owner_id=updater_user_org1.id)
        response_create_main = await authed_client_org1.post("/api/v1/processes/", json=process_to_update_payload)
        assert response_create_main.status_code == 201, response_create_main.text
        process_to_update_id = response_create_main.json()["id"]

        # Attempt to update the process in org1 to have an upstream dependency from org2
        update_payload = ProcessUpdate(upstream_dependency_ids=[process_in_org2.id]).model_dump(mode='json', exclude_unset=True)
        response_update = await authed_client_org1.put(f"/api/v1/processes/{process_to_update_id}", json=update_payload)

        assert response_update.status_code == 404, response_update.text # _get_valid_processes raises 404
        assert "One or more processes not found" in response_update.json()["detail"]
        assert str(process_in_org2.id) in response_update.json()["detail"]

@pytest.mark.asyncio
async def test_update_process_with_invalid_foreign_key_department(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    updater_role = await create_role_with_permissions_async(db_session=async_db_session, role_name=f"UpdInvDeptRole_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE, ProcessPermissions.UPDATE], organization_id=org_id)
    updater_user = await create_user_with_roles_async(db_session=async_db_session, email=f"updinvdept_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org_id, role_names=[updater_role.name])
    async for authed_client in async_client_authenticated_as_user_factory(updater_user):
        valid_dept = await create_test_department_async(async_db_session, organization_id=org_id)
        process_payload = _get_base_process_payload(department_id=valid_dept.id, owner_id=updater_user.id)
        response_create = await authed_client.post("/api/v1/processes/", json=process_payload)
        assert response_create.status_code == 201, response_create.text
        process_id = response_create.json()["id"]

        invalid_dept_id = uuid.uuid4()
        update_payload = ProcessUpdate(department_id=invalid_dept_id).model_dump(mode='json', exclude_unset=True)
        response = await authed_client.put(f"/api/v1/processes/{process_id}", json=update_payload)

        assert response.status_code == 404, response.text
        assert f"Department with ID {invalid_dept_id} not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_process_with_invalid_foreign_key_owner(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    updater_role = await create_role_with_permissions_async(db_session=async_db_session, role_name=f"UpdInvOwnRole_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE, ProcessPermissions.UPDATE], organization_id=org_id)
    updater_user = await create_user_with_roles_async(db_session=async_db_session, email=f"updinvown_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org_id, role_names=[updater_role.name])
    async for authed_client in async_client_authenticated_as_user_factory(updater_user):
        valid_dept = await create_test_department_async(async_db_session, organization_id=org_id)
        process_payload = _get_base_process_payload(department_id=valid_dept.id, owner_id=updater_user.id)
        response_create = await authed_client.post("/api/v1/processes/", json=process_payload)
        assert response_create.status_code == 201, response_create.text
        process_id = response_create.json()["id"]

        invalid_owner_id = uuid.uuid4()
        update_payload = ProcessUpdate(process_owner_id=invalid_owner_id).model_dump(mode='json', exclude_unset=True)
        response = await authed_client.put(f"/api/v1/processes/{process_id}", json=update_payload)

        assert response.status_code == 404, response.text
        assert f"User with ID {invalid_owner_id} not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_process_with_invalid_foreign_key_location(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    updater_role = await create_role_with_permissions_async(db_session=async_db_session, role_name=f"UpdInvLocRole_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE, ProcessPermissions.UPDATE], organization_id=org_id)
    updater_user = await create_user_with_roles_async(db_session=async_db_session, email=f"updinvloc_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org_id, role_names=[updater_role.name])
    async for authed_client in async_client_authenticated_as_user_factory(updater_user):
        valid_dept = await create_test_department_async(async_db_session, organization_id=org_id)
        process_payload = _get_base_process_payload(department_id=valid_dept.id, owner_id=updater_user.id)
        response_create = await authed_client.post("/api/v1/processes/", json=process_payload)
        assert response_create.status_code == 201, response_create.text
        process_id = response_create.json()["id"]

        invalid_location_id = uuid.uuid4()
        update_payload = ProcessUpdate(location_ids=[invalid_location_id]).model_dump(mode='json', exclude_unset=True)
        response = await authed_client.put(f"/api/v1/processes/{process_id}", json=update_payload)

        assert response.status_code == 404, response.text
        assert "One or more locations not found" in response.json()["detail"]
        assert str(invalid_location_id) in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_process_with_invalid_foreign_key_application(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    updater_role = await create_role_with_permissions_async(db_session=async_db_session, role_name=f"UpdInvAppRole_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE, ProcessPermissions.UPDATE], organization_id=org_id)
    updater_user = await create_user_with_roles_async(db_session=async_db_session, email=f"updinvapp_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org_id, role_names=[updater_role.name])
    async for authed_client in async_client_authenticated_as_user_factory(updater_user):
        valid_dept = await create_test_department_async(async_db_session, organization_id=org_id)
        process_payload = _get_base_process_payload(department_id=valid_dept.id, owner_id=updater_user.id)
        response_create = await authed_client.post("/api/v1/processes/", json=process_payload)
        assert response_create.status_code == 201, response_create.text
        process_id = response_create.json()["id"]

        invalid_app_id = uuid.uuid4()
        update_payload = ProcessUpdate(application_ids=[invalid_app_id]).model_dump(mode='json', exclude_unset=True)
        response = await authed_client.put(f"/api/v1/processes/{process_id}", json=update_payload)

        assert response.status_code == 404, response.text
        assert "One or more applications not found" in response.json()["detail"]
        assert str(invalid_app_id) in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_process_with_invalid_foreign_key_dependency(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    updater_role = await create_role_with_permissions_async(db_session=async_db_session, role_name=f"UpdInvDepRole_{uuid.uuid4().hex[:4]}", permissions_names=[ProcessPermissions.CREATE, ProcessPermissions.UPDATE], organization_id=org_id)
    updater_user = await create_user_with_roles_async(db_session=async_db_session, email=f"updinvdep_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org_id, role_names=[updater_role.name])
    async for authed_client in async_client_authenticated_as_user_factory(updater_user):
        valid_dept = await create_test_department_async(async_db_session, organization_id=org_id)
        process_payload = _get_base_process_payload(department_id=valid_dept.id, owner_id=updater_user.id)
        response_create = await authed_client.post("/api/v1/processes/", json=process_payload)
        assert response_create.status_code == 201, response_create.text
        process_id = response_create.json()["id"]

        invalid_process_id = uuid.uuid4()
        update_payload = ProcessUpdate(upstream_dependency_ids=[invalid_process_id]).model_dump(mode='json', exclude_unset=True)
        response = await authed_client.put(f"/api/v1/processes/{process_id}", json=update_payload)

        assert response.status_code == 404, response.text
        assert "One or more processes not found" in response.json()["detail"]
        assert str(invalid_process_id) in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_process_clear_locations(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel,
    default_location_async: LocationModel # Fixture for a location in the same org
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None
    assert default_location_async.organization_id == org_id

    updater_role = await create_role_with_permissions_async(async_db_session, f"ClearLocRole_{uuid.uuid4().hex[:4]}", [ProcessPermissions.CREATE, ProcessPermissions.UPDATE, ProcessPermissions.READ], org_id)
    updater_user = await create_user_with_roles_async(db_session=async_db_session, email=f"clearlocuser_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org_id, role_names=[updater_role.name])
    async for authed_client in async_client_authenticated_as_user_factory(updater_user):
        dept = await create_test_department_async(async_db_session, organization_id=org_id)
        
        # 1. Create process with an initial location
        process_payload = _get_base_process_payload(department_id=dept.id, owner_id=updater_user.id, location_ids=[default_location_async.id])
        response_create = await authed_client.post("/api/v1/processes/", json=process_payload)
        assert response_create.status_code == 201, response_create.text
        process_id = response_create.json()["id"]

        # Verify initial location is set
        # Ensure process_id is defined before this block if create fails or for clarity
        db_process_initial = await ProcessService(async_db_session).get_process_by_id_for_update(uuid.UUID(process_id), org_id)
        assert db_process_initial is not None
        assert len(db_process_initial.locations) == 1
        assert db_process_initial.locations[0].id == default_location_async.id

        # 2. Update to clear locations
        update_payload = ProcessUpdate(location_ids=[]).model_dump(mode='json', exclude_unset=True)
        response_update = await authed_client.put(f"/api/v1/processes/{process_id}", json=update_payload)
        assert response_update.status_code == 200, response_update.text

        # 3. Verify locations are cleared
        await async_db_session.refresh(db_process_initial, attribute_names=['locations'])
        assert len(db_process_initial.locations) == 0

@pytest.mark.asyncio
async def test_update_process_clear_applications(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel,
    default_application_async: ApplicationModel # Fixture for an application in the same org
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None
    assert default_application_async.organization_id == org_id

    updater_role = await create_role_with_permissions_async(async_db_session, f"ClearAppRole_{uuid.uuid4().hex[:4]}", [ProcessPermissions.CREATE, ProcessPermissions.UPDATE, ProcessPermissions.READ], org_id)
    updater_user = await create_user_with_roles_async(db_session=async_db_session, email=f"clearappuser_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org_id, role_names=[updater_role.name])
    async for authed_client in async_client_authenticated_as_user_factory(updater_user):
        dept = await create_test_department_async(async_db_session, organization_id=org_id)

        # 1. Create process with an initial application
        process_payload = _get_base_process_payload(department_id=dept.id, owner_id=updater_user.id, application_ids=[default_application_async.id])
        response_create = await authed_client.post("/api/v1/processes/", json=process_payload)
        assert response_create.status_code == 201, response_create.text
        process_id = response_create.json()["id"]

        db_process_initial = await ProcessService(async_db_session).get_process_by_id_for_update(uuid.UUID(process_id), org_id)
        assert db_process_initial is not None
        assert len(db_process_initial.applications_used) == 1
        assert db_process_initial.applications_used[0].id == default_application_async.id

        # 2. Update to clear applications
        update_payload = ProcessUpdate(application_ids=[]).model_dump(mode='json', exclude_unset=True)
        response_update = await authed_client.put(f"/api/v1/processes/{process_id}", json=update_payload)
        assert response_update.status_code == 200, response_update.text

        # 3. Verify applications are cleared
        await async_db_session.refresh(db_process_initial, attribute_names=['applications_used'])
        assert len(db_process_initial.applications_used) == 0

@pytest.mark.asyncio
async def test_update_process_clear_upstream_dependencies(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    updater_role = await create_role_with_permissions_async(async_db_session, f"ClearUpDepRole_{uuid.uuid4().hex[:4]}", [ProcessPermissions.CREATE, ProcessPermissions.UPDATE, ProcessPermissions.READ], org_id)
    updater_user = await create_user_with_roles_async(db_session=async_db_session, email=f"clearupdepuser_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org_id, role_names=[updater_role.name])
    async for authed_client in async_client_authenticated_as_user_factory(updater_user):
        dept = await create_test_department_async(async_db_session, organization_id=org_id)

        # Create a dependency process
        dep_process_payload = _get_base_process_payload(department_id=dept.id, owner_id=updater_user.id)
        dep_process_payload["name"] = f"UpstreamDepProc_{uuid.uuid4().hex[:4]}"
        response_dep_create = await authed_client.post("/api/v1/processes/", json=dep_process_payload)
        assert response_dep_create.status_code == 201
        dep_process_id = response_dep_create.json()["id"]

        # 1. Create main process with an initial upstream dependency
        process_payload = _get_base_process_payload(department_id=dept.id, owner_id=updater_user.id, upstream_dependency_ids=[dep_process_id])
        response_create = await authed_client.post("/api/v1/processes/", json=process_payload)
        assert response_create.status_code == 201, response_create.text
        process_id = response_create.json()["id"]

        db_process_initial = await ProcessService(async_db_session).get_process_by_id_for_update(uuid.UUID(process_id), org_id)
        assert db_process_initial is not None
        assert len(db_process_initial.upstream_dependencies) == 1
        assert db_process_initial.upstream_dependencies[0].id == uuid.UUID(dep_process_id)

        # 2. Update to clear upstream dependencies
        update_payload = ProcessUpdate(upstream_dependency_ids=[]).model_dump(mode='json', exclude_unset=True)
        response_update = await authed_client.put(f"/api/v1/processes/{process_id}", json=update_payload)
        assert response_update.status_code == 200, response_update.text

        # 3. Verify upstream dependencies are cleared
        await async_db_session.refresh(db_process_initial, attribute_names=['upstream_dependencies'])
        assert len(db_process_initial.upstream_dependencies) == 0

@pytest.mark.asyncio
async def test_update_process_clear_downstream_dependencies(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    updater_role = await create_role_with_permissions_async(async_db_session, f"ClearDownDepRole_{uuid.uuid4().hex[:4]}", [ProcessPermissions.CREATE, ProcessPermissions.UPDATE, ProcessPermissions.READ], org_id)
    updater_user = await create_user_with_roles_async(db_session=async_db_session, email=f"cleardowndepuser_{uuid.uuid4().hex[:6]}@example.com", first_name="TestFirstName", last_name="TestLastName", organization_id=org_id, role_names=[updater_role.name])
    async for authed_client in async_client_authenticated_as_user_factory(updater_user):
        dept = await create_test_department_async(async_db_session, organization_id=org_id)

        # Create a dependency process
        dep_process_payload = _get_base_process_payload(department_id=dept.id, owner_id=updater_user.id)
        dep_process_payload["name"] = f"DownstreamDepProc_{uuid.uuid4().hex[:4]}"
        response_dep_create = await authed_client.post("/api/v1/processes/", json=dep_process_payload)
        assert response_dep_create.status_code == 201
        dep_process_id = response_dep_create.json()["id"]

        # 1. Create main process with an initial downstream dependency
        process_payload = _get_base_process_payload(department_id=dept.id, owner_id=updater_user.id, downstream_dependency_ids=[dep_process_id])
        response_create = await authed_client.post("/api/v1/processes/", json=process_payload)
        assert response_create.status_code == 201, response_create.text
        process_id = response_create.json()["id"]

        db_process_initial = await ProcessService(async_db_session).get_process_by_id_for_update(uuid.UUID(process_id), org_id)
        assert db_process_initial is not None
        assert len(db_process_initial.downstream_dependencies) == 1
        assert db_process_initial.downstream_dependencies[0].id == uuid.UUID(dep_process_id)

        # 2. Update to clear downstream dependencies
        update_payload = ProcessUpdate(downstream_dependency_ids=[]).model_dump(mode='json', exclude_unset=True)
        response_update = await authed_client.put(f"/api/v1/processes/{process_id}", json=update_payload)
        assert response_update.status_code == 200, response_update.text

        # 3. Verify downstream dependencies are cleared
        await async_db_session.refresh(db_process_initial, attribute_names=['downstream_dependencies'])
        assert len(db_process_initial.downstream_dependencies) == 0


# --- RBAC Test Cases for DELETE /processes/{process_id} (Delete Process) ---

@pytest.mark.asyncio
async def test_rbac_delete_process_with_permission(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: User with create + delete permissions
    creator_deleter_role = await create_role_with_permissions_async(
        async_db_session, f"ProcCreatorDeleter_{uuid.uuid4().hex[:4]}", 
        [ProcessPermissions.CREATE, ProcessPermissions.DELETE], 
        org_id
    )
    test_user = await create_user_with_roles_async(
        db_session=async_db_session, email=f"creator_deleter_{uuid.uuid4().hex[:6]}@example.com", 
        first_name="TestFirstName", last_name="TestLastName", 
        role_names=[creator_deleter_role.name], 
        organization_id=org_id
    )
    async for authed_client in async_client_authenticated_as_user_factory(test_user):
        # 2. Create a process to be deleted
        process_to_delete = await _create_test_process_for_rbac(authed_client, async_db_session, org_id, test_user.id)
        process_id_to_delete = process_to_delete.id

        # 3. Action: Attempt to delete the process
        response = await authed_client.delete(f"/api/v1/processes/{process_id_to_delete}")

        # 4. Assert: Expect success (200 OK or 204 No Content)
        # API returns 200 OK with the (now soft-deleted) process data.
        assert response.status_code == 200, response.text 
        response_data = response.json()
        assert response_data["id"] == str(process_id_to_delete)
        assert response_data["is_deleted"] is True
        assert response_data["deleted_at"] is not None

    # 5. Verify in DB that the process is marked as deleted
    process_in_db = await async_db_session.get(ProcessModel, process_id_to_delete)
    assert process_in_db is not None, "Process should still exist in DB after soft delete."
    assert process_in_db.is_deleted is True, "Process should be marked as is_deleted in DB."
    assert process_in_db.deleted_at is not None, "Process deleted_at should be set in DB."

    # Optional: Verify GET returns 404 for the deleted process by a user who *could* read it before deletion.
    # Re-create the client for the same user to ensure fresh state if needed, or use existing.
    # This step requires the user to also have READ permission to attempt the GET.
    # For simplicity, we assume the test_user (creator_deleter) might implicitly have read or we test it separately.
    # If the DELETE endpoint returns the deleted object or a confirmation, this GET might be redundant.
    # For now, we will create a client that also has READ to verify the 404.

    reader_role_for_deleted_check = await create_role_with_permissions_async(
        async_db_session, f"ProcReaderForDeletedCheck_{uuid.uuid4().hex[:4]}", 
        [ProcessPermissions.READ], 
        org_id
    )
    # Ensure the test_user also has this role or create a new user for this check.
    # For this example, let's assume we create a new client for the same user, 
    # and that user's roles are updated/fetched correctly by the factory.
    # A cleaner way might be to give the initial test_user CREATE, DELETE, and READ.
    # Let's adjust the initial role for simplicity for this specific check:
    # Re-creating the user with C+R+D for this check or using a separate user would be more robust.
    # For now, let's assume the `authed_client` can attempt a GET.
    # If `ProcessPermissions.DELETE` implies ability to see it's gone, this is fine.
    # If not, this check needs a user with `ProcessPermissions.READ`.

    # To be safe, let's create a client for a user that definitely has READ to check the 404.
    reader_user = await create_user_with_roles_async(
        async_db_session, f"reader_for_deleted_check_{uuid.uuid4().hex[:6]}@example.com", 
        [reader_role_for_deleted_check.name], 
        org_id
    )
    reader_client = await async_client_authenticated_as_user_factory(reader_user)
    get_response = await reader_client.get(f"/api/v1/processes/{process_id_to_delete}")
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_rbac_delete_process_without_delete_permission(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: User with CREATE permission (to create the process)
    creator_role = await create_role_with_permissions_async(
        async_db_session, f"ProcCreatorForDeleteTest_{uuid.uuid4().hex[:4]}", [ProcessPermissions.CREATE], org_id
    )
    creator_user = await create_user_with_roles_async(
        async_db_session, f"creator_for_delete_{uuid.uuid4().hex[:6]}@example.com", 
        first_name="TestFirstName", last_name="TestLastName", 
        role_names=[creator_role.name], 
        organization_id=org_id
    )
    async for creator_client in async_client_authenticated_as_user_factory(creator_user):
        # 2. Create a process
        process_to_delete = await _create_test_process_for_rbac(creator_client, async_db_session, org_id, creator_user.id)

        # 3. Setup: User with a different permission (e.g., READ) but NOT DELETE
        reader_role = await create_role_with_permissions_async(
            async_db_session, f"ProcReaderForDeleteTest_{uuid.uuid4().hex[:4]}", [ProcessPermissions.READ], org_id
        )
        user_without_delete_perm = await create_user_with_roles_async(
            async_db_session, f"reader_no_delete_{uuid.uuid4().hex[:6]}@example.com", 
            first_name="TestFirstName", last_name="TestLastName", 
            role_names=[reader_role.name], 
            organization_id=org_id
        )
        async for deleter_client in async_client_authenticated_as_user_factory(user_without_delete_perm):
            # 4. Action: Attempt to delete the process
            response = await deleter_client.delete(f"/api/v1/processes/{process_to_delete.id}")

            # 5. Assert: Expect 403 Forbidden
            assert response.status_code == 403, response.text
            response_data = response.json()
    assert "do not have the required permission" in response_data["detail"].lower()
    assert ProcessPermissions.DELETE in response_data["detail"]

@pytest.mark.asyncio
async def test_rbac_delete_process_with_no_relevant_permissions(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: User with CREATE permission to create the process
    creator_role = await create_role_with_permissions_async(
        async_db_session, f"ProcCreatorForNoPermDelete_{uuid.uuid4().hex[:4]}", [ProcessPermissions.CREATE], org_id
    )
    creator_user = await create_user_with_roles_async(
        async_db_session, f"creator_for_noperm_delete_{uuid.uuid4().hex[:6]}@example.com", 
        first_name="TestFirstName", last_name="TestLastName", 
        role_names=[creator_role.name], 
        organization_id=org_id
    )
    creator_client = await async_client_authenticated_as_user_factory(creator_user)

    # 2. Create a process
    process_to_delete = await _create_test_process_for_rbac(creator_client, async_db_session, org_id, creator_user.id)

    # 3. Setup: User with a role that has no process-related permissions
    no_process_perms_role = await create_role_with_permissions_async(
        async_db_session, f"NoProcPermsDeleteRole_{uuid.uuid4().hex[:4]}", ["dummy:other_permission_delete_test"], org_id
    )
    user_with_no_relevant_perms = await create_user_with_roles_async(
        async_db_session, f"noperms_deleter_{uuid.uuid4().hex[:6]}@example.com", [no_process_perms_role.name], org_id
    )
    deleter_client = await async_client_authenticated_as_user_factory(user_with_no_relevant_perms)

    # 4. Action: Attempt to delete the process
    response = await deleter_client.delete(f"/api/v1/processes/{process_to_delete.id}")

    # 5. Assert: Expect 403 Forbidden
    assert response.status_code == 403, response.text
    response_data = response.json()
    assert "do not have the required permission" in response_data["detail"].lower()
    assert ProcessPermissions.DELETE in response_data["detail"]

@pytest.mark.asyncio
async def test_rbac_delete_process_from_different_organization(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel # User from the "main" org
):
    main_org_id = async_default_app_user.organization_id
    assert main_org_id is not None

    # 1. Setup: User and client for the main organization with DELETE permission
    main_org_deleter_role = await create_role_with_permissions_async(
        async_db_session, f"MainOrgProcDeleter_{uuid.uuid4().hex[:4]}", [ProcessPermissions.DELETE], main_org_id
    )
    main_org_user_for_deleting = await create_user_with_roles_async(
        async_db_session, f"main_org_deleter_user_{uuid.uuid4().hex[:6]}@example.com", [main_org_deleter_role.name], main_org_id
    )

    # 2. Setup: Create a "different" organization
    other_org = OrganizationModel(id=uuid.uuid4(), name=f"Other Org For Delete Test {uuid.uuid4().hex[:4]}", industry="Testing")
    async_db_session.add(other_org)
    await async_db_session.flush()

    # 3. Setup: User in "different" org with CREATE permission (to create the target process)
    other_org_creator_role = await create_role_with_permissions_async(
        async_db_session, f"OtherOrgProcCreatorForDelete_{uuid.uuid4().hex[:4]}", [ProcessPermissions.CREATE], other_org.id
    )
    other_org_creator_user = await create_user_with_roles_async(
        async_db_session, f"other_org_creator_for_delete_{uuid.uuid4().hex[:6]}@example.com", [other_org_creator_role.name], other_org.id
    )

    async for other_org_creator_client in async_client_authenticated_as_user_factory(other_org_creator_user):
        # 4. Create a process in the "different" organization
        process_in_other_org = await _create_test_process_for_rbac(other_org_creator_client, async_db_session, other_org.id, other_org_creator_user.id)
        await async_db_session.commit()

        async for main_org_deleter_client in async_client_authenticated_as_user_factory(main_org_user_for_deleting):
            # 5. Action: Attempt to delete the process in "different" org using client from "main" org
            response = await main_org_deleter_client.delete(f"/api/v1/processes/{process_in_other_org.id}")

            # 6. Assert: Expect 403 Forbidden
            assert response.status_code == 403, response.text
            response_data = response.json()
            assert "do not have the required permission" in response_data["detail"].lower()

# --- RBAC Test Cases for GET /processes/ (List Processes) ---

@pytest.mark.asyncio
async def test_rbac_list_processes_with_permission_and_org_scoping(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel # Main org user
):
    main_org_id = async_default_app_user.organization_id
    assert main_org_id is not None

    # 1. Setup: User in main_org with CREATE + READ permissions
    main_org_role = await create_role_with_permissions_async(
        async_db_session, f"MainOrgListReader_{uuid.uuid4().hex[:4]}", 
        [ProcessPermissions.CREATE, ProcessPermissions.LIST], 
        main_org_id
    )
    main_org_user = await create_user_with_roles_async(
        async_db_session, f"main_org_list_reader_{uuid.uuid4().hex[:6]}@example.com", 
        [main_org_role.name], 
        main_org_id
    )
    await async_db_session.commit() # Ensure user/role changes are committed before client uses them

    # Refresh the user to ensure roles and permissions are loaded for the factory
    await async_db_session.refresh(main_org_user, attribute_names=['roles'])
    for role in main_org_user.roles:
        await async_db_session.refresh(role, attribute_names=['permissions'])

    async for main_org_client in async_client_authenticated_as_user_factory(main_org_user):
        # 2. Create processes in main_org
        proc1_main_org = await _create_test_process_for_rbac(main_org_client, async_db_session, main_org_id, main_org_user.id)
        proc2_main_org = await _create_test_process_for_rbac(main_org_client, async_db_session, main_org_id, main_org_user.id)

        # 3. Setup: Create a "different" organization and a user/process within it
        other_org = OrganizationModel(id=uuid.uuid4(), name=f"Other Org List Test {uuid.uuid4().hex[:4]}", industry="Testing")
        async_db_session.add(other_org)
        await async_db_session.flush()

        other_org_role = await create_role_with_permissions_async(
            async_db_session, f"OtherOrgListCreator_{uuid.uuid4().hex[:4]}", [ProcessPermissions.CREATE], other_org.id
        )
        other_org_user = await create_user_with_roles_async(
            async_db_session, f"other_org_list_creator_{uuid.uuid4().hex[:6]}@example.com", [other_org_role.name], other_org.id
        )
        async for other_org_client in async_client_authenticated_as_user_factory(other_org_user):
            _ = await _create_test_process_for_rbac(other_org_client, async_db_session, other_org.id, other_org_user.id) # Process in other_org

        await async_db_session.commit()

        # 4. Action: Main org user lists processes
        response = await main_org_client.get("/api/v1/processes/")

        # 5. Assert: Expect success (200 OK) and only processes from main_org are listed
        assert response.status_code == 200, response.text
        response_data = response.json()
    
    assert isinstance(response_data, list)
    process_ids_in_response = {item["id"] for item in response_data}
    
    assert str(proc1_main_org.id) in process_ids_in_response
    assert str(proc2_main_org.id) in process_ids_in_response
    # Check that processes from other_org are NOT in the list
    # This requires knowing the ID of the process created in other_org, or checking count if predictable.
    # For now, we assert that the number of processes is as expected for main_org.
    # A more robust check would be to ensure no process in the list has organization_id == other_org.id
    for item in response_data:
        assert item["organization_id"] == str(main_org_id)
    # Assuming only these two processes were created for this org by this test setup for this user.
    # This might be fragile if other tests run concurrently or if there's existing data.
    # A more specific check is that only main_org_id processes are returned.
    assert len(response_data) >= 2 # At least the two we created, could be more if other tests ran.

@pytest.mark.asyncio
async def test_rbac_list_processes_without_read_permission(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: User with a permission OTHER THAN 'process:read' (e.g., 'process:create')
    # Note: The _create_test_process_for_rbac helper requires CREATE perm on the client it uses.
    # So, we need a user who can create, and another user who tries to list without read perm.

    creator_role = await create_role_with_permissions_async(
        async_db_session, f"ListCreatorOnly_{uuid.uuid4().hex[:4]}", [ProcessPermissions.CREATE], org_id
    )
    creator_user = await create_user_with_roles_async(
        async_db_session, f"list_creator_only_{uuid.uuid4().hex[:6]}@example.com", [creator_role.name], org_id
    )
    async for creator_client in async_client_authenticated_as_user_factory(creator_user):
        await _create_test_process_for_rbac(creator_client, async_db_session, org_id, creator_user.id) # Create a process

        # User who will attempt to list, has only UPDATE permission
        updater_only_role = await create_role_with_permissions_async(
            async_db_session, f"ListUpdaterOnly_{uuid.uuid4().hex[:4]}", [ProcessPermissions.UPDATE], org_id
        )
        user_without_read_perm = await create_user_with_roles_async(
            async_db_session, f"list_updater_no_read_{uuid.uuid4().hex[:6]}@example.com", [updater_only_role.name], org_id
        )
        async for lister_client in async_client_authenticated_as_user_factory(user_without_read_perm):
            # 2. Action: Attempt to list processes
            response = await lister_client.get("/api/v1/processes/")

            # 3. Assert: Expect 403 Forbidden
            assert response.status_code == 403, response.text
            response_data = response.json()
            assert "do not have the required permission" in response_data["detail"].lower()
            assert ProcessPermissions.LIST in response_data["detail"]

@pytest.mark.asyncio
async def test_rbac_list_processes_with_no_relevant_permissions(
    async_client_authenticated_as_user_factory,
    async_db_session: AsyncSession,
    async_default_app_user: UserModel
):
    org_id = async_default_app_user.organization_id
    assert org_id is not None

    # 1. Setup: Create a process first (requires a user with create perm)
    creator_role = await create_role_with_permissions_async(
        async_db_session, f"ListCreatorForNoPerm_{uuid.uuid4().hex[:4]}", [ProcessPermissions.CREATE], org_id
    )
    creator_user = await create_user_with_roles_async(
        db_session=async_db_session, 
        email=f"list_creator_for_noperm_{uuid.uuid4().hex[:6]}@example.com", 
        first_name="TestFirstName", 
        last_name="TestLastName", 
        organization_id=org_id, 
        role_names=[creator_role.name]
    )
    async for creator_client in async_client_authenticated_as_user_factory(creator_user):
        await _create_test_process_for_rbac(creator_client, async_db_session, org_id, creator_user.id)

        # User with a role that has no process-related permissions
        no_process_perms_role = await create_role_with_permissions_async(
            async_db_session, f"NoProcPermsListRole_{uuid.uuid4().hex[:4]}", ["dummy:other_permission_list_test"], org_id
        )
        user_with_no_relevant_perms = await create_user_with_roles_async(
            async_db_session, f"noperms_lister_{uuid.uuid4().hex[:6]}@example.com", [no_process_perms_role.name], org_id
        )
        async for lister_client in async_client_authenticated_as_user_factory(user_with_no_relevant_perms):
            # 2. Action: Attempt to list processes
            response = await lister_client.get("/api/v1/processes/")

            # 3. Assert: Expect 403 Forbidden
            assert response.status_code == 403, response.text
            response_data = response.json()
            assert "do not have the required permission" in response_data["detail"].lower()
            assert ProcessPermissions.LIST in response_data["detail"]
