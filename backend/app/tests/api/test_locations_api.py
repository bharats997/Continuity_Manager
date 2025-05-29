# backend/app/tests/api/test_locations_api.py
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from backend.app.models.domain.organizations import Organization as OrganizationModel
from backend.app.models.location import LocationCreate, LocationUpdate

# Helper to create an organization directly in the DB for tests
def create_test_organization(db: Session, name: str = "Test Organization") -> OrganizationModel:
    org = OrganizationModel(name=name, description="A test organization")
    db.add(org)
    db.commit()
    db.refresh(org)
    return org

@pytest.mark.asyncio
async def test_create_location(test_client: AsyncClient, db_session: Session):
    # 1. Create a prerequisite organization
    org = create_test_organization(db_session, name="OrgForLocTest")
    org_id = org.id # Get ID before expunging
    if org in db_session:
        db_session.expunge(org)
        print(f"DEBUG [test_locations_api]: Expunged org (ID: {org_id}) from test session {db_session} in test_create_location.")

    # 2. Prepare location data
    location_data = LocationCreate(
        name="Main Office",
        address_line1="123 Test St",
        city="Testville",
        country="Testland",
        organizationId=org_id  # Link to the created organization
    )

    # 3. Make the API request to create a location
    response = await test_client.post("/api/v1/locations/", json=location_data.model_dump())

    # 4. Assert the response
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == location_data.name
    assert data["address_line1"] == location_data.address_line1
    assert data["city"] == location_data.city
    assert data["country"] == location_data.country
    assert data["organizationId"] == org_id
    assert "id" in data

@pytest.mark.asyncio
async def test_read_location(test_client: AsyncClient, db_session: Session):
    # 1. Create a prerequisite organization and location
    org = create_test_organization(db_session, name="OrgForReadLocTest")
    org_id = org.id # Get ID before expunging
    if org in db_session:
        db_session.expunge(org)
        print(f"DEBUG [test_locations_api]: Expunged org (ID: {org_id}) from test session {db_session} in test_read_location.")

    location_create_data = LocationCreate(
        name="Branch Office",
        address_line1="456 Branch Ave",
        city="Branchburg",
        country="Testland",
        organizationId=org_id
    )  # Create location directly via service or API for setup
    # For simplicity, let's assume direct creation or use the API if preferred
    # Here, we'll use the API to ensure the create endpoint works as a prerequisite
    create_response = await test_client.post("/api/v1/locations/", json=location_create_data.model_dump())
    assert create_response.status_code == 201
    created_location_id = create_response.json()["id"]

    # 2. Make the API request to read the location
    response = await test_client.get(f"/api/v1/locations/{created_location_id}")

    # 3. Assert the response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_location_id
    assert data["name"] == location_create_data.name
    assert data["organizationId"] == org_id

@pytest.mark.asyncio
async def test_read_locations_for_organization(test_client: AsyncClient, db_session: Session):
    org1 = create_test_organization(db_session, name="OrgWithLocations")
    org2 = create_test_organization(db_session, name="OrgWithoutLocations")

    # Get IDs before expunging, as accessing attributes post-expunge can be problematic
    org1_id = org1.id
    # org2_id = org2.id # Not strictly needed for this test's API calls but good practice

    if org1 in db_session:
        db_session.expunge(org1)
        print(f"DEBUG [test_locations_api]: Expunged org1 (ID: {org1_id}) from test session {db_session}.")
    if org2 in db_session:
        db_session.expunge(org2)
        print(f"DEBUG [test_locations_api]: Expunged org2 from test session {db_session}.")
    
    loc1_data = LocationCreate(name="HQ", address_line1="1 Main St", city="Capital", country="Testland", organizationId=org1_id)
    loc2_data = LocationCreate(name="Warehouse", address_line1="2 Storage Rd", city="Depot", country="Testland", organizationId=org1_id)
    
    await test_client.post("/api/v1/locations/", json=loc1_data.model_dump())
    await test_client.post("/api/v1/locations/", json=loc2_data.model_dump())

    response = await test_client.get(f"/api/v1/locations/organization/{org1_id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2 # Assuming the total count is accurate
    assert len(data["items"]) == 2
    assert {item["name"] for item in data["items"]} == {"HQ", "Warehouse"}

    response_org2 = await test_client.get(f"/api/v1/locations/organization/{org2.id}/")
    assert response_org2.status_code == 200
    data_org2 = response_org2.json()
    assert data_org2["total"] == 0
    assert len(data_org2["items"]) == 0


@pytest.mark.asyncio
async def test_update_location(test_client: AsyncClient, db_session: Session):
    org = create_test_organization(db_session, name="OrgForUpdateTest")
    org_id = org.id
    if org in db_session:
        db_session.expunge(org)

    location_create_data = LocationCreate(
        name="Original Location Name",
        address_line1="1 Original St",
        city="Original City",
        country="Testland",
        organizationId=org_id
    )
    create_response = await test_client.post("/api/v1/locations/", json=location_create_data.model_dump())
    assert create_response.status_code == 201
    created_location_id = create_response.json()["id"]

    location_update_data = LocationUpdate(
        name="Updated Location Name",
        address_line1="123 Updated Ave",
        city="Updated City"
    )

    response = await test_client.put(f"/api/v1/locations/{created_location_id}", json=location_update_data.model_dump(exclude_unset=True))
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_location_id
    assert data["name"] == location_update_data.name
    assert data["address_line1"] == location_update_data.address_line1
    assert data["city"] == location_update_data.city
    assert data["country"] == location_create_data.country # Country was not updated
    assert data["organizationId"] == org_id

@pytest.mark.asyncio
async def test_update_location_not_found(test_client: AsyncClient, db_session: Session):
    non_existent_location_id = 99999
    location_update_data = LocationUpdate(name="Attempted Update")
    response = await test_client.put(f"/api/v1/locations/{non_existent_location_id}", json=location_update_data.model_dump())
    assert response.status_code == 404
    assert response.json()["detail"] == "Location not found"

@pytest.mark.asyncio
async def test_delete_location(test_client: AsyncClient, db_session: Session):
    org = create_test_organization(db_session, name="OrgForDeleteTest")
    org_id = org.id
    if org in db_session:
        db_session.expunge(org)

    location_create_data = LocationCreate(
        name="Location To Delete",
        address_line1="1 Delete St",
        city="Deleteville",
        country="Testland",
        organizationId=org_id
    )
    create_response = await test_client.post("/api/v1/locations/", json=location_create_data.model_dump())
    assert create_response.status_code == 201
    created_location_data = create_response.json()
    created_location_id = created_location_data["id"]

    delete_response = await test_client.delete(f"/api/v1/locations/{created_location_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["id"] == created_location_id
    assert delete_response.json()["name"] == location_create_data.name

    # Verify it's actually deleted by trying to fetch it
    get_response = await test_client.get(f"/api/v1/locations/{created_location_id}")
    assert get_response.status_code == 404 # Service's get_location doesn't raise 404, API endpoint does

@pytest.mark.asyncio
async def test_delete_location_not_found(test_client: AsyncClient, db_session: Session):
    non_existent_location_id = 99998
    response = await test_client.delete(f"/api/v1/locations/{non_existent_location_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Location not found"

@pytest.mark.asyncio
async def test_create_location_non_existent_org(test_client: AsyncClient, db_session: Session):
    non_existent_org_id = 99997
    location_data = LocationCreate(
        name="Location with Bad Org",
        address_line1="1 Invalid St",
        city="Invalidville",
        country="Testland",
        organizationId=non_existent_org_id
    )
    response = await test_client.post("/api/v1/locations/", json=location_data.model_dump())
    assert response.status_code == 404 # Service raises 404 for non-existent organization
    assert f"Organization with id {non_existent_org_id} not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_location_duplicate_name_in_org(test_client: AsyncClient, db_session: Session):
    org = create_test_organization(db_session, name="OrgForDuplicateLocTest")
    org_id = org.id
    if org in db_session:
        db_session.expunge(org)

    location_data_1 = LocationCreate(
        name="Duplicate Name Office",
        address_line1="1 First St",
        city="Testville",
        country="Testland",
        organizationId=org_id
    )
    response1 = await test_client.post("/api/v1/locations/", json=location_data_1.model_dump())
    assert response1.status_code == 201

    location_data_2 = LocationCreate(
        name="Duplicate Name Office", # Same name
        address_line1="2 Second St",
        city="Testville",
        country="Testland",
        organizationId=org_id # Same organization
    )
    response2 = await test_client.post("/api/v1/locations/", json=location_data_2.model_dump())
    assert response2.status_code == 400 # Service raises 400 for duplicate name in org
    assert f"Location with name '{location_data_2.name}' already exists in this organization." in response2.json()["detail"]
