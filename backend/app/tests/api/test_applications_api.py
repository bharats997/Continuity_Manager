# backend/app/tests/api/test_applications_api.py
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from typing import Dict

from backend.app.models.domain.organizations import Organization as OrganizationModel
from backend.app.models.domain.people import Person as PersonModel
from backend.app.models.application import ApplicationCreate, ApplicationUpdate

# --- Helper Functions ---
def create_test_organization(db: Session, name: str = "Test Org for Apps", description: str = "Org Desc") -> OrganizationModel:
    org = OrganizationModel(name=name, description=description, industry="Tech")
    db.add(org)
    db.commit()
    db.refresh(org)
    return org

def create_test_person(db: Session, organization_id: int, name: str = "Test User for Apps", email_suffix: str = "apptest") -> PersonModel:
    # Ensure email is unique if there's a unique constraint
    email = f"{name.lower().replace(' ', '.')}.{email_suffix}@example.com"
    name_parts = name.split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else "User" # Default last name

    person = PersonModel(
        firstName=first_name,
        lastName=last_name,
        email=email,
        jobTitle="Tester",
        departmentId=None, # Assuming department is optional or to be handled separately
        organizationId=organization_id,
        # password_hash would be set if direct user creation involved passwords
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person

# --- Test Cases ---

@pytest.mark.asyncio
async def test_create_application(test_client: AsyncClient, db_session: Session):
    # 1. Create prerequisite organization and app owner (person)
    org = create_test_organization(db_session, name="AppCreate Org")
    app_owner = create_test_person(db_session, organization_id=org.id, name="App Owner One")
    
    org_id = org.id
    app_owner_id = app_owner.id

    # Expunge to ensure fresh load by API if necessary
    if org in db_session: db_session.expunge(org)
    if app_owner in db_session: db_session.expunge(app_owner)

    # 2. Prepare application data
    application_data = ApplicationCreate(
        name="My Critical App",
        description="A very important application for testing.",
        organizationId=org_id,
        appOwnerId=app_owner_id,
        applicationType="Custom Developed",
        hostingEnvironment="Cloud",
        criticality="High",
        isActive=True
    )

    # 3. Make the API request
    # Assuming test_client handles authentication and current_user is set
    response = await test_client.post("/api/v1/applications/", json=application_data.model_dump())

    # 4. Assert the response
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == application_data.name
    assert data["description"] == application_data.description
    assert data["organizationId"] == org_id
    assert data["appOwnerId"] == app_owner_id
    assert data["applicationType"] == application_data.applicationType
    assert data["hostingEnvironment"] == application_data.hostingEnvironment
    assert data["criticality"] == application_data.criticality
    assert data["isActive"] == application_data.isActive
    assert "id" in data
    assert "createdAt" in data
    assert "updatedAt" in data
    assert data["creator"] is not None # Assuming current_user is populated by the endpoint
    assert data["updater"] is not None
    assert data["organization"] is not None
    assert data["organization"]["id"] == org_id
    assert data["appOwner"] is not None
    assert data["appOwner"]["id"] == app_owner_id

@pytest.mark.asyncio
async def test_create_application_minimal_data(test_client: AsyncClient, db_session: Session):
    org = create_test_organization(db_session, name="AppCreate Min Org")
    org_id = org.id
    if org in db_session: db_session.expunge(org)

    application_data = ApplicationCreate(
        name="Minimal App",
        organizationId=org_id
        # appOwnerId is optional
    )
    response = await test_client.post("/api/v1/applications/", json=application_data.model_dump())
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == application_data.name
    assert data["organizationId"] == org_id
    assert data["appOwnerId"] is None
    assert data["appOwner"] is None
    assert data["isActive"] is True # Default value

@pytest.mark.asyncio
async def test_create_application_invalid_organization_id(test_client: AsyncClient, db_session: Session):
    non_existent_org_id = 99999
    application_data = ApplicationCreate(
        name="App With Bad Org",
        organizationId=non_existent_org_id
    )
    response = await test_client.post("/api/v1/applications/", json=application_data.model_dump())
    assert response.status_code == 400, response.text # Service raises ValueError
    assert f"Organization with id {non_existent_org_id} not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_application_invalid_app_owner_id(test_client: AsyncClient, db_session: Session):
    org = create_test_organization(db_session, name="AppCreate Invalid Owner Org")
    org_id = org.id
    if org in db_session: db_session.expunge(org)
    
    non_existent_owner_id = 88888
    application_data = ApplicationCreate(
        name="App With Bad Owner",
        organizationId=org_id,
        appOwnerId=non_existent_owner_id
    )
    response = await test_client.post("/api/v1/applications/", json=application_data.model_dump())
    assert response.status_code == 400, response.text # Service raises ValueError
    assert f"App owner with id {non_existent_owner_id} not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_application(test_client: AsyncClient, db_session: Session):
    org = create_test_organization(db_session, name="AppRead Org")
    app_owner = create_test_person(db_session, organization_id=org.id, name="App Owner Two")
    org_id = org.id
    app_owner_id = app_owner.id
    if org in db_session: db_session.expunge(org)
    if app_owner in db_session: db_session.expunge(app_owner)

    # Create an application via API to test reading it
    app_create_data = ApplicationCreate(
        name="Readable App", organizationId=org_id, appOwnerId=app_owner_id
    )
    create_response = await test_client.post("/api/v1/applications/", json=app_create_data.model_dump())
    assert create_response.status_code == 201, create_response.text
    created_app_id = create_response.json()["id"]

    # Read the application
    response = await test_client.get(f"/api/v1/applications/{created_app_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == created_app_id
    assert data["name"] == app_create_data.name
    assert data["organizationId"] == org_id
    assert data["appOwnerId"] == app_owner_id
    assert data["organization"]["id"] == org_id
    assert data["appOwner"]["id"] == app_owner_id

@pytest.mark.asyncio
async def test_read_application_not_found(test_client: AsyncClient, db_session: Session):
    non_existent_app_id = 77777
    response = await test_client.get(f"/api/v1/applications/{non_existent_app_id}")
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Application not found"

@pytest.mark.asyncio
async def test_read_applications_empty(test_client: AsyncClient, db_session: Session):
    response = await test_client.get("/api/v1/applications/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

@pytest.mark.asyncio
async def test_read_applications_list(test_client: AsyncClient, db_session: Session):
    org1 = create_test_organization(db_session, name="AppList Org1")
    owner1 = create_test_person(db_session, organization_id=org1.id, name="Owner List1")

    org1_id = org1.id
    owner1_id = owner1.id

    if org1 in db_session: db_session.expunge(org1)
    if owner1 in db_session: db_session.expunge(owner1)

    app1_data = ApplicationCreate(name="App X", organizationId=org1_id, appOwnerId=owner1_id)
    app2_data = ApplicationCreate(name="App Y", organizationId=org1_id) # No owner

    await test_client.post("/api/v1/applications/", json=app1_data.model_dump())
    await test_client.post("/api/v1/applications/", json=app2_data.model_dump())

    response = await test_client.get("/api/v1/applications/")
    assert response.status_code == 200, response.text
    data = response.json()
    # Check for at least 2, as other tests might leave data if not perfectly isolated or cleaned.
    # A better approach in a full test suite would be to ensure clean state or specific filtering.
    assert len(data) >= 2 
    
    names_in_org1 = {app['name'] for app in data if app['organizationId'] == org1_id}
    assert "App X" in names_in_org1
    assert "App Y" in names_in_org1

@pytest.mark.asyncio
async def test_read_applications_pagination_and_filtering(test_client: AsyncClient, db_session: Session):
    org_filter = create_test_organization(db_session, name="OrgForFilterApps")
    org_other = create_test_organization(db_session, name="OrgOtherAppsList")
    owner_filter = create_test_person(db_session, organization_id=org_filter.id, name="Owner FilterApps")

    org_filter_id = org_filter.id
    org_other_id = org_other.id
    owner_filter_id = owner_filter.id

    if org_filter in db_session: db_session.expunge(org_filter)
    if org_other in db_session: db_session.expunge(org_other)
    if owner_filter in db_session: db_session.expunge(owner_filter)

    created_app_names_for_org_filter = []
    for i in range(3):
        app_name = f"FilterApp{i+1}"
        created_app_names_for_org_filter.append(app_name)
        app_data = ApplicationCreate(name=app_name, organizationId=org_filter_id, appOwnerId=owner_filter_id)
        await test_client.post("/api/v1/applications/", json=app_data.model_dump())
    
    app_other_data = ApplicationCreate(name="OtherOrgAppForList", organizationId=org_other_id)
    await test_client.post("/api/v1/applications/", json=app_other_data.model_dump())

    # Test filtering by organizationId
    response_filtered = await test_client.get(f"/api/v1/applications/?organization_id={org_filter_id}")
    assert response_filtered.status_code == 200, response_filtered.text
    data_filtered = response_filtered.json()
    assert len(data_filtered) == 3
    for app in data_filtered:
        assert app['organizationId'] == org_filter_id

    # Test pagination with filter (assuming default order or stable order for test)
    # To make this more robust, sort by a known field if order isn't guaranteed by default (e.g. name)
    response_paginated = await test_client.get(f"/api/v1/applications/?organization_id={org_filter_id}&skip=1&limit=1")
    assert response_paginated.status_code == 200, response_paginated.text
    data_paginated = response_paginated.json()
    assert len(data_paginated) == 1
    # Check if the paginated app name is one of the created app names for that org
    assert data_paginated[0]['name'] in created_app_names_for_org_filter 

@pytest.mark.asyncio
async def test_update_application(test_client: AsyncClient, db_session: Session):
    org = create_test_organization(db_session, name="AppUpdate OrgMain")
    owner_orig = create_test_person(db_session, organization_id=org.id, name="Owner OrigUpd")
    owner_new = create_test_person(db_session, organization_id=org.id, name="Owner NewUpd")

    org_id = org.id
    owner_orig_id = owner_orig.id
    owner_new_id = owner_new.id

    if org in db_session: db_session.expunge(org)
    if owner_orig in db_session: db_session.expunge(owner_orig)
    if owner_new in db_session: db_session.expunge(owner_new)

    app_create_data = ApplicationCreate(
        name="Original App Name", organizationId=org_id, appOwnerId=owner_orig_id,
        description="Original Description", criticality="Medium"
    )
    create_response = await test_client.post("/api/v1/applications/", json=app_create_data.model_dump())
    assert create_response.status_code == 201, create_response.text
    created_app_id = create_response.json()["id"]

    update_payload = ApplicationUpdate(
        name="Updated App Name", description="Updated Description",
        appOwnerId=owner_new_id, criticality="High", isActive=False
    )
    response = await test_client.put(f"/api/v1/applications/{created_app_id}", json=update_payload.model_dump(exclude_unset=True))
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == created_app_id
    assert data["name"] == update_payload.name
    assert data["description"] == update_payload.description
    assert data["appOwnerId"] == owner_new_id
    assert data["appOwner"]["id"] == owner_new_id
    assert data["criticality"] == update_payload.criticality
    assert data["isActive"] == update_payload.isActive

@pytest.mark.asyncio
async def test_update_application_not_found(test_client: AsyncClient, db_session: Session):
    non_existent_app_id = 66666
    update_payload = ApplicationUpdate(name="Attempted Update")
    response = await test_client.put(f"/api/v1/applications/{non_existent_app_id}", json=update_payload.model_dump(exclude_unset=True))
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Application not found"

@pytest.mark.asyncio
async def test_update_application_invalid_owner(test_client: AsyncClient, db_session: Session):
    org = create_test_organization(db_session, name="AppUpdate InvalidOwner Org2")
    org_id = org.id
    if org in db_session: db_session.expunge(org)

    app_create_data = ApplicationCreate(name="App For Invalid Owner Update2", organizationId=org_id)
    create_response = await test_client.post("/api/v1/applications/", json=app_create_data.model_dump())
    assert create_response.status_code == 201, create_response.text
    created_app_id = create_response.json()["id"]

    non_existent_owner_id = 55555
    update_payload = ApplicationUpdate(appOwnerId=non_existent_owner_id)
    response = await test_client.put(f"/api/v1/applications/{created_app_id}", json=update_payload.model_dump(exclude_unset=True))
    assert response.status_code == 400, response.text
    assert f"App owner with id {non_existent_owner_id} not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_application(test_client: AsyncClient, db_session: Session):
    org = create_test_organization(db_session, name="AppDelete OrgMain")
    org_id = org.id
    if org in db_session: db_session.expunge(org)

    app_create_data = ApplicationCreate(name="App To Be Deleted", organizationId=org_id)
    create_response = await test_client.post("/api/v1/applications/", json=app_create_data.model_dump())
    assert create_response.status_code == 201, create_response.text
    created_app_id = create_response.json()["id"]

    delete_response = await test_client.delete(f"/api/v1/applications/{created_app_id}")
    assert delete_response.status_code == 200, delete_response.text
    deleted_data = delete_response.json()
    assert deleted_data["id"] == created_app_id
    assert deleted_data["isActive"] is False
    assert deleted_data["deletedAt"] is not None

    get_response = await test_client.get(f"/api/v1/applications/{created_app_id}")
    assert get_response.status_code == 404, get_response.text

@pytest.mark.asyncio
async def test_delete_application_not_found(test_client: AsyncClient, db_session: Session):
    non_existent_app_id = 44444
    response = await test_client.delete(f"/api/v1/applications/{non_existent_app_id}")
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Application not found"

@pytest.mark.asyncio
async def test_delete_already_deleted_application(test_client: AsyncClient, db_session: Session):
    org = create_test_organization(db_session, name="AppDeleteTwice Org2")
    org_id = org.id
    if org in db_session: db_session.expunge(org)

    app_create_data = ApplicationCreate(name="App To Be Deleted Twice Again", organizationId=org_id)
    create_response = await test_client.post("/api/v1/applications/", json=app_create_data.model_dump())
    assert create_response.status_code == 201, create_response.text
    created_app_id = create_response.json()["id"]

    await test_client.delete(f"/api/v1/applications/{created_app_id}") # First delete
    
    # Second delete attempt should result in 404 because get_application in the endpoint filters soft-deleted items
    delete_response_again = await test_client.delete(f"/api/v1/applications/{created_app_id}")
    assert delete_response_again.status_code == 404, delete_response_again.text
    assert delete_response_again.json()["detail"] == "Application not found"

