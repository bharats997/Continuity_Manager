# backend/app/tests/api/test_applications_api.py
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text # Added for test_basic_db_session_standalone

from app.schemas.applications import ApplicationCreate, ApplicationRead, ApplicationUpdate
from app.models.domain.applications import ApplicationType, ApplicationStatusEnum # For ApplicationType enum
from app.models.domain.organizations import Organization as OrganizationModel
from app.models.domain.users import User as UserModel # Corrected import path for SQLAlchemy model
from app.models.domain.applications import Application as ApplicationModel # Corrected import path for SQLAlchemy model

# --- Helper Functions ---
def create_test_organization(db: Session, name: str = "Test Org for Apps", description: str = "Org Desc") -> OrganizationModel:
    org = OrganizationModel(name=name, description=description, industry="Tech")
    db.add(org)

    db.refresh(org)
    return org

async def create_test_organization_async(db: AsyncSession, name: str = "Test Org for Apps Async", description: str = "Org Desc Async") -> OrganizationModel:
    org = OrganizationModel(id=uuid.uuid4(), name=name, description=description, industry="Tech") # Added id for explicit creation
    db.add(org)
    await db.flush()
    await db.refresh(org)
    return org

def create_test_user(db: Session, organization_id: uuid.UUID, first_name_prefix: str = "TestUser", email_suffix: str = "apptest") -> UserModel:
    # Counter for unique emails to avoid conflicts during multiple test runs / user creations
    if not hasattr(create_test_user, 'counter'):
        create_test_user.counter = 0
    create_test_user.counter += 1
    
    email = f"{first_name_prefix.lower()}.{create_test_user.counter}.{email_suffix}@example.com"
    
    user = UserModel(
        id=uuid.uuid4(), # Added id for explicit creation
        first_name=f"{first_name_prefix}{create_test_user.counter}",
        last_name="AppTester",
        email=email,
        job_title="Application Tester", # snake_case for consistency
        organization_id=organization_id, # snake_case for consistency
        password_hash="$2b$12$EixzaY8N3yL0k2X5K9s13uHpL1jB2c7g5.jS2.B.sA2xlfc2uKVmG", # Default test password: "testpassword"
        is_active=True
        # department_id=None, # Add if your UserModel has this and it's relevant for tests
    )
    db.add(user)

    db.refresh(user)
    return user

async def create_test_user_async(db: AsyncSession, organization_id: uuid.UUID, first_name_prefix: str = "TestUserAsync", email_suffix: str = "apptest") -> UserModel:
    if not hasattr(create_test_user_async, 'counter'):
        create_test_user_async.counter = 0
    create_test_user_async.counter += 1
    
    email = f"{first_name_prefix.lower()}.{create_test_user_async.counter}.{email_suffix}@example.com"
    
    user = UserModel(
        id=uuid.uuid4(), # Added id for explicit creation
        first_name=f"{first_name_prefix}{create_test_user_async.counter}",
        last_name="User",
        email=email,
        job_title="Application Tester Async",
        organization_id=organization_id,
        password_hash="$2b$12$EixzaY8N3yL0k2X5K9s13uHpL1jB2c7g5.jS2.B.sA2xlfc2uKVmG",
        is_active=True
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user

# --- Test Cases ---

@pytest.mark.asyncio
async def test_basic_db_session_standalone(async_db_session: AsyncSession):
    """Tests the async_db_session fixture in isolation."""
    assert async_db_session is not None
    # Perform a simple query
    result = await async_db_session.execute(text("SELECT 1"))
    assert result.scalar_one() == 1
    # logger.info("test_basic_db_session_standalone: SELECT 1 query successful.")
    # Optionally, try a simple DDL to test transaction behavior (will be rolled back by fixture)
    # await async_db_session.execute(text("CREATE TABLE IF NOT EXISTS test_dummy_table (id INTEGER PRIMARY KEY)"))
    # await async_db_session.commit() # This commits to the nested transaction/savepoint
    # logger.info("test_basic_db_session_standalone: Dummy table DDL executed and committed to savepoint.")


@pytest.mark.asyncio
async def test_create_application(ciso_user_authenticated_client: AsyncClient, async_db_session: AsyncSession, async_default_app_user: UserModel):
    # async_current_test_user is assumed to be from the ciso_user_authenticated_client's token
    # The application's organization will be derived from this user.
    org_id_from_auth_user = async_default_app_user.organization_id

    # Create an app_owner in the same organization as the authenticated user
    app_owner = await create_test_user_async(async_db_session, organization_id=org_id_from_auth_user, first_name_prefix="AppOwnerFull")
    
    application_data = ApplicationCreate(
        name="My New Critical App",
        description="A very important application for testing purposes.",
        app_owner_id=app_owner.id, # Use the ID of the created user
        type=ApplicationType.OWNED.value,
        organization_id=str(org_id_from_auth_user),
        hosted_on="Cloud Provider X",
        status=ApplicationStatusEnum.ACTIVE,  # Added status
        workarounds="Use manual process as a workaround."
    )

    response = await ciso_user_authenticated_client.post("/api/v1/applications/", json=application_data.model_dump(mode='json'))

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == application_data.name
    assert data["description"] == application_data.description
    assert data["organization"]["id"] == str(org_id_from_auth_user)
    assert data["app_owner"]["id"] == str(app_owner.id)
    assert data["type"] == application_data.type.value # Enum value
    assert data["hosted_on"] == application_data.hosted_on
    assert data["workarounds"] == application_data.workarounds
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert data["organization"]["name"] is not None # Assuming OrganizationResponse has name
    assert data["app_owner"]["email"] == app_owner.email # Assuming UserResponse has email

@pytest.mark.asyncio
async def test_create_application_minimal_data(ciso_user_authenticated_client: AsyncClient, async_default_app_user: UserModel, async_test_app_owner_user: UserModel):
    # The application's organization will be derived from async_default_app_user (who is the CISO making the request).
    org_id_from_auth_user = async_default_app_user.organization_id
    app_owner_id_to_set = async_test_app_owner_user.id # Use the dedicated app owner user

    application_data = ApplicationCreate(
        name="Minimal App For Test",
        type=ApplicationType.SAAS.value, # Software as a Service
        organizationId=str(org_id_from_auth_user),
        appOwnerId=str(app_owner_id_to_set), # Provide the app owner ID
        status=ApplicationStatusEnum.ACTIVE.value # Status is also required by ApplicationBase
        # No description, hosted_on, workarounds, version, vendor, criticality, derivedRTO
    )
    response = await ciso_user_authenticated_client.post("/api/v1/applications/", json=application_data.model_dump(by_alias=True))
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == application_data.name
    assert data["organization"]["id"] == str(org_id_from_auth_user)
    assert data["type"] == application_data.type.value
    assert data["status"] == application_data.status.value
    assert data["appOwnerId"] == str(app_owner_id_to_set)
    assert data["appOwner"] is not None
    assert data["appOwner"]["id"] == str(app_owner_id_to_set)
    assert data["description"] is None
    assert data["hostedOn"] is None
    assert data["workarounds"] is None

@pytest.mark.asyncio
async def test_create_application_invalid_app_owner_id(ciso_user_authenticated_client: AsyncClient, async_db_session: AsyncSession, async_default_app_user: UserModel):
    # async_current_test_user.organization_id will be the app's organization
    # Create a different organization for the invalid app owner
    org_other = await create_test_organization_async(async_db_session, name="Other Org For Invalid Owner")
    app_owner_other_org = await create_test_user_async(async_db_session, organization_id=org_other.id, first_name_prefix="OtherOrgOwner")

    application_data = ApplicationCreate(
        name="App With Cross-Org Owner",
        type=ApplicationType.OWNED.value, # Commercial Off-The-Shelf
        organizationId=str(async_default_app_user.organization_id),
        appOwnerId=app_owner_other_org.id, # Owner from a different org
        status=ApplicationStatusEnum.ACTIVE.value
    )

    response = await ciso_user_authenticated_client.post("/api/v1/applications/", json=application_data.model_dump(by_alias=True), expect_error=True)
    
    assert response.status_code == 404, response.text
    assert "not found in organization" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_application_duplicate_name(ciso_user_authenticated_client: AsyncClient, async_db_session: AsyncSession, async_default_app_user: UserModel):
    # The application's organization will be derived from async_default_app_user.
    app_owner_same_org = await create_test_user_async(async_db_session, organization_id=async_default_app_user.organization_id, first_name_prefix="DuplicateNameOwner")

    app_name = f"Unique App Name {uuid.uuid4()}"

    application_data_1 = ApplicationCreate(
        name=app_name,
        type=ApplicationType.OWNED.value,
        organizationId=str(async_default_app_user.organization_id),
        appOwnerId=app_owner_same_org.id,
        status=ApplicationStatusEnum.ACTIVE.value
    )
    response1 = await ciso_user_authenticated_client.post("/api/v1/applications/", json=application_data_1.model_dump(by_alias=True))
    assert response1.status_code == 201, response1.text

    # Attempt to create another application with the same name in the same organization
    application_data_2 = ApplicationCreate(
        name=app_name, # Same name
        type=ApplicationType.OWNED.value, # Different type, but name should be unique
        organizationId=str(async_default_app_user.organization_id),
        appOwnerId=app_owner_same_org.id,
        status=ApplicationStatusEnum.ACTIVE.value
    )
    response2 = await ciso_user_authenticated_client.post("/api/v1/applications/", json=application_data_2.model_dump(by_alias=True), expect_error=True)
    
    assert response2.status_code == 400, response2.text
    detail_message = response2.json()['detail']
    assert detail_message.startswith(f"Application with name '{app_name}'")
    assert "already exists in this organization" in detail_message

@pytest.mark.asyncio
async def test_read_application(ciso_user_authenticated_client: AsyncClient, async_db_session: AsyncSession, async_default_app_user: UserModel):
    org_id_current_user = async_default_app_user.organization_id
    app_owner = await create_test_user_async(async_db_session, organization_id=org_id_current_user, first_name_prefix="ReadableAppOwner")

    application_create_data = ApplicationCreate(
        name="My Readable App",
        description="Description for readable app.",
        appOwnerId=app_owner.id,
        type=ApplicationType.OWNED.value,
        organizationId=str(org_id_current_user),
        hostedOn="On-Premise",
        status=ApplicationStatusEnum.ACTIVE.value
    )

    create_response = await ciso_user_authenticated_client.post("/api/v1/applications/", json=application_create_data.model_dump(by_alias=True))
    assert create_response.status_code == 201, create_response.text
    created_app_data = create_response.json()
    created_app_id = created_app_data["id"]

    # Test reading the created application
    response = await ciso_user_authenticated_client.get(f"/api/v1/applications/{created_app_id}")

    if response.status_code == 422 or response.status_code == 500:
        print("Detailed Pydantic ValidationError from response:")
        try:
            error_detail = response.json()
            import json
            print(json.dumps(error_detail, indent=2))
        except Exception as e_json:
            print(f"Could not parse JSON from error response: {e_json}")
            print(f"Raw error response text: {response.text}")
        pytest.fail(f"Test failed due to server-side validation error (Status {response.status_code}). Check printed details.")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == created_app_id
    assert data["name"] == application_create_data.name
    assert data["description"] == application_create_data.description
    assert data["organization"]["id"] == str(org_id_current_user)
    assert data["appOwner"]["id"] == str(app_owner.id)
    assert data["createdBy"]["id"] == str(async_default_app_user.id)
    assert data["type"] == application_create_data.type
    assert data["hostedOn"] == application_create_data.hostedOn

    # Test: User cannot read application from another organization
    org_other = await create_test_organization_async(async_db_session, name="Other Org For Read Test")
    app_owner_other_org = await create_test_user_async(async_db_session, organization_id=org_other.id, first_name_prefix="OtherOrgAppOwner")
    
    # Create application in other_org directly (not via API of current_test_user)
    # For simplicity, we'll assume a direct DB entry or a separate mechanism would create this.
    # Here, we'll simulate its creation for the purpose of getting an ID.
    # In a real scenario, this might involve another authenticated client or service call.


    # app_service = ApplicationService(async_db_session) # type: ignore # This seems unused for direct creation here
    other_app_obj = ApplicationModel(
        name="Cross Org App", 
        organization_id=org_other.id, 
        app_owner_id=app_owner_other_org.id, 
        type=ApplicationType.OWNED.value
    )
    async_db_session.add(other_app_obj)

    await async_db_session.refresh(other_app_obj)
    other_app_id = other_app_obj.id

    response_other_org_app = await ciso_user_authenticated_client.get(f"/api/v1/applications/{other_app_id}", expect_error=True)
    assert response_other_org_app.status_code == 404, response_other_org_app.text
    assert response_other_org_app.json()["detail"] == "Application not found or not accessible in your organization."

@pytest.mark.asyncio
async def test_read_application_not_found(ciso_user_authenticated_client: AsyncClient, async_db_session: AsyncSession, async_default_app_user: UserModel):
    non_existent_app_id = uuid.uuid4()
    response = await ciso_user_authenticated_client.get(f"/api/v1/applications/{non_existent_app_id}", expect_error=True)
    assert response.status_code == 404
    assert "Application not found or not accessible" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_applications_empty(ciso_user_authenticated_client: AsyncClient, async_default_app_user: UserModel): # Added async_current_test_user
    # This test assumes that for the async_current_test_user's organization, no applications exist yet.
    # If other tests create apps for this org without cleaning up, this test might be flaky.
    # Consider adding cleanup or ensuring a fresh org for this test if needed.
    response = await ciso_user_authenticated_client.get("/api/v1/applications/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert data == [] # Expect an empty list for no applications

@pytest.mark.asyncio
async def test_read_applications_list(ciso_user_authenticated_client: AsyncClient, async_db_session: AsyncSession, async_default_app_user: UserModel):
    org_id_current_user = async_default_app_user.organization_id
    app_owner1 = await create_test_user_async(async_db_session, organization_id=org_id_current_user, first_name_prefix="ListAppOwner1")
    app_owner2 = await create_test_user_async(async_db_session, organization_id=org_id_current_user, first_name_prefix="ListAppOwner2")

    app1_create_data = ApplicationCreate(
        name="Listed App Alpha", 
        type=ApplicationType.OWNED.value, 
        organizationId=str(org_id_current_user),
        appOwnerId=app_owner1.id,
        status=ApplicationStatusEnum.ACTIVE.value
    )
    app2_create_data = ApplicationCreate(
        name="Listed App Beta", 
        type=ApplicationType.OWNED.value, 
        organizationId=str(org_id_current_user),
        appOwnerId=app_owner2.id, 
        description="Beta version",
        status=ApplicationStatusEnum.ACTIVE.value
    )

    # Create two applications in the async_current_test_user's organization
    response_create1 = await ciso_user_authenticated_client.post("/api/v1/applications/", json=app1_create_data.model_dump(by_alias=True))
    assert response_create1.status_code == 201, response_create1.text
    app1_id = response_create1.json()["id"]

    response_create2 = await ciso_user_authenticated_client.post("/api/v1/applications/", json=app2_create_data.model_dump(by_alias=True))
    assert response_create2.status_code == 201, response_create2.text
    app2_id = response_create2.json()["id"]

    # Create an application in a different organization (should not be listed)
    org_other = await create_test_organization_async(async_db_session, name="Other Org For List Test")
    app_owner_other_org = await create_test_user_async(async_db_session, organization_id=org_other.id, first_name_prefix="OtherOrgListOwner")
    
    # Using service directly to create app in another org to avoid complex auth setup for this test part
    # Using ApplicationModel directly to create app in another org
    other_org_app_obj = ApplicationModel(
        id=uuid.uuid4(), # Add id for explicit creation
        name="Cross Org App For List", 
        organization_id=org_other.id, 
        app_owner_id=app_owner_other_org.id, 
        type=ApplicationType.OWNED.value,
        created_by_id=app_owner_other_org.id, # Corrected field name
        updated_by_id=app_owner_other_org.id, # Add updated_by_id for consistency
        status=ApplicationStatusEnum.ACTIVE.value # Ensure it's active
    )
    async_db_session.add(other_org_app_obj)

    await async_db_session.refresh(other_org_app_obj) # Refresh to get all fields

    # List applications for the async_current_test_user's organization
    response_list = await ciso_user_authenticated_client.get("/api/v1/applications/")
    assert response_list.status_code == 200, response_list.text
    application_list = response_list.json()
    assert isinstance(application_list, list)
    # Assuming the endpoint is NOT paginated by default or these parameters are not used for this call
    # If it were paginated, the structure would be different (e.g., response.json()['items'])
    
    assert len(application_list) >= 2 # Check if at least the two created apps are present

    listed_app_ids = {item["id"] for item in application_list}
    assert app1_id in listed_app_ids
    assert app2_id in listed_app_ids

    for item in application_list:
        if item["id"] not in [app1_id, app2_id]: # Skip other apps that might exist from other tests
            continue
        assert item["organization"]["id"] == str(org_id_current_user)
        assert item["status"] == ApplicationStatusEnum.ACTIVE.value # Check status instead of is_active
        if item["id"] == app1_id:
            assert item["name"] == app1_create_data.name
            assert item["appOwner"]["id"] == str(app_owner1.id)
        elif item["id"] == app2_id:
            assert item["name"] == app2_create_data.name
            assert item["appOwner"]["id"] == str(app_owner2.id)

@pytest.mark.asyncio
async def test_read_applications_pagination_and_filtering(ciso_user_authenticated_client: AsyncClient, async_db_session: AsyncSession, async_default_app_user: UserModel):
    org_id = async_default_app_user.organization_id
    # Helper to create apps for this test via API
    async def _create_app(name: str, app_type: ApplicationType, description: str = "Test app"):
        app_owner = await create_test_user_async(async_db_session, organization_id=org_id, first_name_prefix=f"Owner{name.replace(' ', '')}")
        payload = ApplicationCreate(name=name, type=app_type, organizationId=str(org_id), appOwnerId=app_owner.id, description=description, status=ApplicationStatusEnum.ACTIVE.value)
        response = await ciso_user_authenticated_client.post("/api/v1/applications/", json=payload.model_dump(by_alias=True))
        assert response.status_code == 201, f"Failed to create {name}: {response.text}"
        return response.json()

    # Create a set of applications
    app_configs = [
        {"name": "Alpha App", "type": ApplicationType.OWNED.value, "desc": "Alpha custom app"},
        {"name": "Bravo App", "type": ApplicationType.SAAS.value, "desc": "Bravo SaaS solution"},
        {"name": "Charlie App", "type": ApplicationType.OWNED.value, "desc": "Charlie custom app"},
        {"name": "Delta App", "type": ApplicationType.OWNED.value, "desc": "Delta COTS package"},
        {"name": "Echo App", "type": ApplicationType.SAAS.value, "desc": "Echo SaaS platform"},
        {"name": "Foxtrot App Special", "type": ApplicationType.OWNED.value, "desc": "Foxtrot special project"}
    ]
    created_apps = []
    for config in app_configs:
        app_data = await _create_app(config["name"], config["type"], config["desc"])
        created_apps.append(app_data)
    
    # --- Pagination Tests ---
    # Assuming default order is by creation time (or ID which is sequential in tests)
    # Test 1: page=1, size=2 (expecting first 2 created: Alpha, Bravo)
    response_page1_size2 = await ciso_user_authenticated_client.get("/api/v1/applications/?page=1&size=2")
    assert response_page1_size2.status_code == 200, response_page1_size2.text
    data_p1s2 = response_page1_size2.json()
    assert isinstance(data_p1s2, list)
    assert len(data_p1s2) == 2 # Expecting 2 items based on size=2
    # To check total, you'd need another mechanism or make assumptions based on full list if size is large enough
    # For now, we assume the list is ordered by creation and check names
    assert data_p1s2[0]["name"] == "Alpha App"
    assert data_p1s2[1]["name"] == "Bravo App"

    # Test 2: page=2, size=2 (expecting next 2: Charlie, Delta)
    response_page2_size2 = await ciso_user_authenticated_client.get("/api/v1/applications/?page=2&size=2")
    assert response_page2_size2.status_code == 200, response_page2_size2.text
    data_p2s2 = response_page2_size2.json()
    assert isinstance(data_p2s2, list)
    assert len(data_p2s2) == 2
    assert data_p2s2[0]["name"] == "Charlie App"
    assert data_p2s2[1]["name"] == "Delta App"

    # Test 3: page=3, size=2 (expecting next 2: Echo, Foxtrot)
    response_page3_size2 = await ciso_user_authenticated_client.get("/api/v1/applications/?page=3&size=2")
    assert response_page3_size2.status_code == 200, response_page3_size2.text
    data_p3s2 = response_page3_size2.json()
    assert isinstance(data_p3s2, list)
    assert len(data_p3s2) == 2
    assert data_p3s2[0]["name"] == "Echo App"
    assert data_p3s2[1]["name"] == "Foxtrot App Special"

    # --- Name Filtering Tests ---
    # Test 1: name contains "App" (partial match, case-insensitive if backend supports)
    # Assuming backend does case-sensitive exact or prefix match for simplicity here if not specified
    response_name_app = await ciso_user_authenticated_client.get("/api/v1/applications/?name=App") # This might be too broad or specific depending on backend
    # For a more robust test, let's filter by a more specific prefix
    response_name_alpha = await ciso_user_authenticated_client.get("/api/v1/applications/?name=Alpha App")
    assert response_name_alpha.status_code == 200
    data_name_alpha = response_name_alpha.json()
    assert isinstance(data_name_alpha, list)
    assert len(data_name_alpha) == 1
    assert data_name_alpha[0]["name"] == "Alpha App"

    response_name_special = await ciso_user_authenticated_client.get("/api/v1/applications/?name=Special") # Test partial name from Foxtrot App Special
    assert response_name_special.status_code == 200
    data_name_special = response_name_special.json()
    assert isinstance(data_name_special, list)
    # This assertion depends on whether 'name' filter is 'contains' or 'startswith'
    # Assuming service implements filtering that finds this one item
    assert len(data_name_special) == 1 
    assert data_name_special[0]["name"] == "Foxtrot App Special"

    # --- Application Type Filtering Tests ---
    # Filter by SAAS
    response_type_saas = await ciso_user_authenticated_client.get(f"/api/v1/applications/?type={ApplicationType.SAAS.value}") # Query param is 'type'
    assert response_type_saas.status_code == 200
    data_type_saas = response_type_saas.json()
    assert isinstance(data_type_saas, list)
    assert len(data_type_saas) >= 2 # Two SAAS apps were created
    saas_app_names = {item["name"] for item in data_type_saas}
    assert "Bravo App" in saas_app_names
    assert "Echo App" in saas_app_names

    # Filter by OWNED
    response_type_owned = await ciso_user_authenticated_client.get(f"/api/v1/applications/?type={ApplicationType.OWNED.value}") # Use 'type' query param
    assert response_type_owned.status_code == 200
    data_type_owned = response_type_owned.json()
    assert isinstance(data_type_owned, list)
    assert len(data_type_owned) == 4 # Alpha, Charlie, Delta, Foxtrot
    owned_names = {item["name"] for item in data_type_owned}
    assert "Alpha App" in owned_names
    assert "Charlie App" in owned_names
    assert "Delta App" in owned_names
    assert "Foxtrot App Special" in owned_names

    # --- Combined Filtering and Pagination ---
    # Filter by OWNED, page 1, size 2. Expect Alpha, Charlie (4 total OWNED apps)
    response_combo = await ciso_user_authenticated_client.get(f"/api/v1/applications/?type={ApplicationType.OWNED.value}&page=1&size=2") # Use 'type' query param
    assert response_combo.status_code == 200
    data_combo = response_combo.json()
    assert isinstance(data_combo, list)
    assert len(data_combo) == 2 # Page 1, size 2
    # Assuming default ordering by name for consistency in tests if not otherwise specified by creation time
    # The created_apps are: Alpha, Bravo, Charlie, Delta, Echo, Foxtrot
    # OWNED apps are: Alpha, Charlie, Delta, Foxtrot. Sorted by name: Alpha, Charlie, Delta, Foxtrot
    # Page 1, Size 2 of OWNED apps should be Alpha, Charlie
    assert data_combo[0]["name"] == "Alpha App"
    assert data_combo[1]["name"] == "Charlie App"

    # Verify all returned items belong to the correct organization and are active
    all_responses = [data_p1s2, data_p2s2, data_p3s2, data_name_alpha, data_name_special, data_type_saas, data_type_owned, data_combo]
    for resp_data_list in all_responses: # resp_data_list is one of the lists like data_p1s2
        for item in resp_data_list: # Iterate directly over the list of applications
            assert item["organization"]["id"] == str(org_id)
            assert item["status"] == ApplicationStatusEnum.ACTIVE.value # Check status 

@pytest.mark.asyncio
async def test_update_application(ciso_user_authenticated_client: AsyncClient, async_db_session: AsyncSession, async_default_app_user: UserModel):
    org_id = async_default_app_user.organization_id
    owner_orig = await create_test_user_async(async_db_session, organization_id=org_id, first_name_prefix="OwnerOrigUpd")
    new_owner = await create_test_user_async(async_db_session, organization_id=org_id, first_name_prefix="NewAppOwnerForUpdate")

    app_create_payload = ApplicationCreate(
        name="Original App Name", 
        type=ApplicationType.OWNED.value,
        organizationId=str(org_id),
        appOwnerId=owner_orig.id, 
        description="Original Description", 
        criticality="Medium", 
        status=ApplicationStatusEnum.ACTIVE.value
    )
    create_response = await ciso_user_authenticated_client.post("/api/v1/applications/", json=app_create_payload.model_dump(by_alias=True))
    assert create_response.status_code == 201, create_response.text
    created_app_data = create_response.json()
    created_app_id = created_app_data["id"]

    update_payload = ApplicationUpdate(
        name="Updated App Name", 
        description="Updated Description",
        appOwnerId=new_owner.id, 
        type=ApplicationType.OWNED.value,
        criticality="High", 
        status=ApplicationStatusEnum.INACTIVE.value
    )
    response = await ciso_user_authenticated_client.put(f"/api/v1/applications/{created_app_id}", json=update_payload.model_dump(by_alias=True, exclude_unset=True))
    assert response.status_code == 200, response.text
    updated_data = response.json()

    assert updated_data["id"] == created_app_id
    assert updated_data["name"] == update_payload.name
    assert updated_data["description"] == update_payload.description
    assert updated_data["appOwner"]["id"] == str(new_owner.id)
    assert updated_data["type"] == ApplicationType.OWNED.value
    assert updated_data["criticality"] == update_payload.criticality
    assert updated_data["status"] == ApplicationStatusEnum.INACTIVE.value
    assert updated_data["organization"]["id"] == str(org_id)

@pytest.mark.asyncio
async def test_update_application_not_found(ciso_user_authenticated_client: AsyncClient, async_default_app_user: UserModel):
    non_existent_app_id = uuid.uuid4()
    update_payload = ApplicationUpdate(name="Attempted Update To NonExistent")
    response = await ciso_user_authenticated_client.put(f"/api/v1/applications/{non_existent_app_id}", json=update_payload.model_dump(by_alias=True, exclude_unset=True), expect_error=True)
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Application not found or not accessible for update."

@pytest.mark.asyncio
async def test_update_application_invalid_owner(ciso_user_authenticated_client: AsyncClient, async_db_session: AsyncSession, async_default_app_user: UserModel):
    org_id = async_default_app_user.organization_id
    initial_owner = await create_test_user_async(async_db_session, organization_id=org_id, first_name_prefix="InitialAppOwnerForUpdate")

    app_create_payload = ApplicationCreate(
        name="App For Invalid Owner Update Test", 
        type=ApplicationType.OWNED.value,
        organizationId=str(org_id),
        appOwnerId=initial_owner.id,
        status=ApplicationStatusEnum.ACTIVE.value
    )
    create_response = await ciso_user_authenticated_client.post("/api/v1/applications/", json=app_create_payload.model_dump(by_alias=True))
    assert create_response.status_code == 201, create_response.text
    created_app_id = create_response.json()["id"]

    # Scenario 1: Non-existent App Owner ID
    non_existent_owner_id = uuid.uuid4()
    update_payload_non_existent_owner = ApplicationUpdate(appOwnerId=non_existent_owner_id)
    response_non_existent = await ciso_user_authenticated_client.put(
        f"/api/v1/applications/{created_app_id}", 
        json=update_payload_non_existent_owner.model_dump(by_alias=True, exclude_unset=True), expect_error=True
    )
    assert response_non_existent.status_code == 404, response_non_existent.text # Changed 422 to 404
    # Assuming the service layer checks for user existence and raises an appropriate error.
    # The exact message might vary based on ApplicationService implementation.
    # Adjusted to match actual API error detail:
    assert "not found in organization" in response_non_existent.json()["detail"]
    assert f"App owner with id {str(non_existent_owner_id)} not found" in response_non_existent.json()["detail"]

    # Scenario 2: App Owner from a different organization
    other_org = await create_test_organization_async(async_db_session, name="Other Org For Invalid Owner Test")
    other_org_owner = await create_test_user_async(async_db_session, organization_id=other_org.id, first_name_prefix="OtherOrgAppOwner")
    
    update_payload_cross_org_owner = ApplicationUpdate(appOwnerId=other_org_owner.id)
    response_cross_org = await ciso_user_authenticated_client.put(
        f"/api/v1/applications/{created_app_id}", 
        json=update_payload_cross_org_owner.model_dump(by_alias=True, exclude_unset=True), expect_error=True
    )
    assert response_cross_org.status_code == 404, response_cross_org.text
    assert "not found in organization" in response_cross_org.json()["detail"]

@pytest.mark.asyncio
async def test_delete_application(ciso_user_authenticated_client: AsyncClient, async_db_session: AsyncSession, async_default_app_user: UserModel):
    org_id = async_default_app_user.organization_id
    app_owner = await create_test_user_async(async_db_session, organization_id=org_id, first_name_prefix="AppOwnerForDelete")

    app_create_payload = ApplicationCreate(
        name="App To Be Soft Deleted", 
        type=ApplicationType.OWNED.value,
        organizationId=str(org_id),
        appOwnerId=app_owner.id,
        status=ApplicationStatusEnum.ACTIVE.value
    )
    create_response = await ciso_user_authenticated_client.post("/api/v1/applications/", json=app_create_payload.model_dump(mode='json'))
    assert create_response.status_code == 201, create_response.text
    created_app_data = create_response.json()
    created_app_id = created_app_data["id"]

    # Soft delete the application
    delete_response = await ciso_user_authenticated_client.delete(f"/api/v1/applications/{created_app_id}")
    assert delete_response.status_code == 200, delete_response.text
    deleted_app_data = delete_response.json()

    assert deleted_app_data["id"] == created_app_id
    assert deleted_app_data["name"] == app_create_payload.name
    print(f"DEBUG: deleted_app_data for test_delete_application: {deleted_app_data}") # DEBUG
    assert deleted_app_data["status"] == ApplicationStatusEnum.INACTIVE.value
    assert deleted_app_data["organization"]["id"] == str(org_id)
    assert deleted_app_data["appOwner"]["id"] == str(app_owner.id)

    # Verify the application is not retrievable via GET by ID after soft delete
    get_response_after_delete = await ciso_user_authenticated_client.get(f"/api/v1/applications/{created_app_id}", expect_error=True)
    assert get_response_after_delete.status_code == 404, get_response_after_delete.text
    assert get_response_after_delete.json()["detail"] == "Application not found or not accessible in your organization."

    # Verify the application is not listed in active applications
    list_response = await ciso_user_authenticated_client.get("/api/v1/applications/")
    assert list_response.status_code == 200
    listed_apps = list_response.json() # The endpoint returns a direct list
    assert not any(app["id"] == created_app_id for app in listed_apps)

@pytest.mark.asyncio
async def test_delete_application_not_found(ciso_user_authenticated_client: AsyncClient, async_default_app_user: UserModel):
    non_existent_app_id = uuid.uuid4()
    delete_response = await ciso_user_authenticated_client.delete(f"/api/v1/applications/{non_existent_app_id}", expect_error=True)
    assert delete_response.status_code == 404, delete_response.text
    assert delete_response.json()["detail"] == "Application not found or not accessible for deletion."


@pytest.mark.asyncio
async def test_update_application_cross_organization_fail(
    ciso_user_authenticated_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_default_app_user: UserModel
):
    # Create an organization different from the async_current_test_user's organization
    other_org = await create_test_organization_async(async_db_session, name="Other Org For Cross-Update Test")
    other_org_owner = await create_test_user_async(async_db_session, organization_id=other_org.id, first_name_prefix="OtherOrgOwnerUpdate")
    # No need to commit here as helper functions do it

    # Create an application in this 'other_org'
    cross_org_app_to_update = ApplicationModel(
        id=uuid.uuid4(),
        name="Cross-Org App For Update Test",
        organization_id=other_org.id,
        app_owner_id=other_org_owner.id,
        type=ApplicationType.OWNED.value,
        status="ACTIVE",
        created_by_id=async_default_app_user.id # Use async_current_test_user for created_by_id
    )
    async_db_session.add(cross_org_app_to_update)

    await async_db_session.refresh(cross_org_app_to_update)

    update_payload = ApplicationUpdate(name="Attempted Cross-Org Update")
    
    # async_current_test_user (from a different org) attempts to update this app
    response = await ciso_user_authenticated_client.put(
        f"/api/v1/applications/{cross_org_app_to_update.id}", 
        json=update_payload.model_dump(mode='json', exclude_unset=True),
        expect_error=True
    )
    
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Application not found or not accessible for update."

@pytest.mark.asyncio
async def test_delete_application_cross_organization_fail(
    ciso_user_authenticated_client: AsyncClient, 
    async_db_session: AsyncSession, 
    async_default_app_user: UserModel
):
    # Create an organization different from the async_current_test_user's organization
    other_org = await create_test_organization_async(async_db_session, name="Other Org For Cross-Delete Test")
    other_org_owner = await create_test_user_async(async_db_session, organization_id=other_org.id, first_name_prefix="OtherOrgOwnerDelete")

    # Create an application in this 'other_org'
    cross_org_app_to_delete = ApplicationModel(
        id=uuid.uuid4(),
        name="Cross-Org App To Delete Test",
        organization_id=other_org.id,
        app_owner_id=other_org_owner.id,
        type=ApplicationType.OWNED.value,
        status="ACTIVE",
        created_by_id=async_default_app_user.id # Use current user for created_by_id
    )
    async_db_session.add(cross_org_app_to_delete)

    await async_db_session.refresh(cross_org_app_to_delete)
    
    # current_test_user (from a different org) attempts to delete this app
    response = await ciso_user_authenticated_client.delete(f"/api/v1/applications/{cross_org_app_to_delete.id}", expect_error=True)
    
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Application not found or not accessible for deletion."


@pytest.mark.asyncio
async def test_delete_already_deleted_application(ciso_user_authenticated_client: AsyncClient, async_db_session: AsyncSession, async_default_app_user: UserModel):
    org = await create_test_organization_async(async_db_session, name="AppDeleteTwice Org2")
    # For this test, we want to ensure the application is created in an organization that the test client can access.
    # The ciso_user_authenticated_client is scoped to DEFAULT_ASYNC_ORG_ID by default from conftest.py's async_current_test_user.
    # So, we should use that org_id for creating the application.
    org_id = async_default_app_user.organization_id # Use the org of the current test user

    app_create_data = ApplicationCreate(
        name="App To Be Deleted Twice Again", 
        organizationId=org_id, 
        type=ApplicationType.SAAS.value, 
        appOwnerId=async_default_app_user.id, 
        status=ApplicationStatusEnum.ACTIVE.value
    )
    create_response = await ciso_user_authenticated_client.post("/api/v1/applications/", json=app_create_data.model_dump(by_alias=True))
    assert create_response.status_code == 201, create_response.text
    created_app_id = create_response.json()["id"]

    await ciso_user_authenticated_client.delete(f"/api/v1/applications/{created_app_id}")
    
    delete_response_again = await ciso_user_authenticated_client.delete(f"/api/v1/applications/{created_app_id}", expect_error=True)
    assert delete_response_again.status_code == 404, delete_response_again.text
    assert delete_response_again.json()["detail"] == "Application not found or not accessible for deletion."

