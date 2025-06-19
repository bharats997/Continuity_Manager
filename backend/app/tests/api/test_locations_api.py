# backend/app/tests/api/test_locations_api.py
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.domain.organizations import Organization as OrganizationModel
from app.schemas.location import LocationCreate, LocationUpdate
from app.tests.helpers import DEFAULT_ORG_ID

# Helper to create an organization directly in the DB for tests
def create_test_organization(db: Session, name: str = "Test Organization") -> OrganizationModel:
    org = OrganizationModel(name=name, description="A test organization")
    db.add(org)
    db.commit()
    db.refresh(org)
    return org

@pytest.mark.asyncio
async def test_create_location(test_client: AsyncClient, db_session: Session):
    location_data = LocationCreate(
        name="Main Office Test Create",
        address_line1="123 Test St",
        city="Testville",
        country="Testland",
        organizationId=DEFAULT_ORG_ID
    )

    response = await test_client.post(f"/api/v1/locations/", json=location_data.model_dump(mode='json'))

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == location_data.name
    assert data["address_line1"] == location_data.address_line1
    assert data["city"] == location_data.city
    assert data["country"] == location_data.country
    assert data["organizationId"] == str(DEFAULT_ORG_ID)
    assert "id" in data

@pytest.mark.asyncio
async def test_read_location(test_client: AsyncClient, db_session: Session):
    location_create_data = LocationCreate(
        name="Readable Location Test",
        address_line1="456 Read Ave",
        city="Readville",
        country="Testland",
        organizationId=DEFAULT_ORG_ID
    )
    create_response = await test_client.post("/api/v1/locations/", json=location_create_data.model_dump(mode='json'))
    assert create_response.status_code == 201
    created_location_id = create_response.json()["id"]

    response = await test_client.get(f"/api/v1/locations/{created_location_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_location_id
    assert data["name"] == location_create_data.name
    assert data["organizationId"] == str(DEFAULT_ORG_ID)

@pytest.mark.asyncio
async def test_read_locations_for_organization(test_client: AsyncClient, db_session: Session):
    org1 = create_test_organization(db_session, name="OrgWithLocations")
    org2 = create_test_organization(db_session, name="OrgWithoutLocations")

    org1_id = org1.id

    if org1 in db_session:
        db_session.expunge(org1)
    if org2 in db_session:
        db_session.expunge(org2)
    
    loc1_data = LocationCreate(name="HQ List Test", address_line1="1 Main St List", city="Capital List", country="Testland List", organizationId=DEFAULT_ORG_ID)
    loc2_data = LocationCreate(name="Warehouse List Test", address_line1="2 Storage Rd List", city="Depot List", country="Testland List", organizationId=DEFAULT_ORG_ID)
    
    response_loc1 = await test_client.post("/api/v1/locations/", json=loc1_data.model_dump(mode='json'))
    assert response_loc1.status_code == 201
    response_loc2 = await test_client.post("/api/v1/locations/", json=loc2_data.model_dump(mode='json'))
    assert response_loc2.status_code == 201

    response = await test_client.get(f"/api/v1/locations/organization/{DEFAULT_ORG_ID}/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert {item["name"] for item in data["items"]} == {"HQ List Test", "Warehouse List Test"}

    response_org2 = await test_client.get(f"/api/v1/locations/organization/{org2.id}/")
    assert response_org2.status_code == 403
    data_org2 = response_org2.json()
    assert "detail" in data_org2
    assert data_org2["detail"] == "Not authorized to access locations for this organization"


@pytest.mark.asyncio
async def test_update_location(test_client: AsyncClient, db_session: Session):
    location_create_data = LocationCreate(
        name="Original Location Name For Update", 
        address_line1="1 Original St",
        city="Original City",
        country="Testland",
        organizationId=DEFAULT_ORG_ID  
    )  
    create_response = await test_client.post("/api/v1/locations/", json=location_create_data.model_dump(mode='json'))
    assert create_response.status_code == 201
    created_location_id = create_response.json()["id"]

    location_update_data = LocationUpdate(
        name="Updated Location Name",
        address_line1="123 Updated Ave",
        city="Updated City"
    )

    response = await test_client.put(f"/api/v1/locations/{created_location_id}", json=location_update_data.model_dump(mode='json', exclude_unset=True))
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_location_id
    assert data["name"] == location_update_data.name
    assert data["address_line1"] == location_update_data.address_line1
    assert data["city"] == location_update_data.city
    assert data["country"] == location_create_data.country
    assert data["organizationId"] == str(DEFAULT_ORG_ID)

@pytest.mark.asyncio
async def test_update_location_not_found(test_client: AsyncClient, db_session: Session):
    non_existent_location_id = str(uuid.uuid4())
    location_update_data = LocationUpdate(name="Attempted Update")
    response = await test_client.put(f"/api/v1/locations/{non_existent_location_id}", json=location_update_data.model_dump(mode='json'))
    assert response.status_code == 404
    assert response.json()["detail"] == "Location not found"

@pytest.mark.asyncio
async def test_delete_location(test_client: AsyncClient, db_session: Session):
    location_create_data = LocationCreate(
        name="Location To Delete Test",
        address_line1="1 Delete St",
        city="Deleteville",
        country="Testland",
        organizationId=DEFAULT_ORG_ID
    )
    create_response = await test_client.post("/api/v1/locations/", json=location_create_data.model_dump(mode='json'))
    assert create_response.status_code == 201
    created_location_data = create_response.json()
    created_location_id = created_location_data["id"]

    delete_response = await test_client.delete(f"/api/v1/locations/{created_location_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["id"] == created_location_id
    assert delete_response.json()['name'] == location_create_data.name

    get_response = await test_client.get(f"/api/v1/locations/{created_location_id}")
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_delete_location_not_found(test_client: AsyncClient, db_session: Session):
    non_existent_location_id = str(uuid.uuid4())
    response = await test_client.delete(f"/api/v1/locations/{non_existent_location_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Location not found"

@pytest.mark.asyncio
async def test_create_location_non_existent_org(test_client: AsyncClient, db_session: Session):
    non_existent_org_id = str(uuid.uuid4())
    location_data = LocationCreate(
        name="Location with Bad Org",
        address_line1="1 Invalid St",
        city="Invalidville",
        country="Testland",
        organizationId=non_existent_org_id
    )
    response = await test_client.post(f"/api/v1/locations/", json=location_data.model_dump(mode='json'))
    assert response.status_code == 403
    assert "You do not have permission to create locations for this organization." in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_location_duplicate_name_in_org(test_client: AsyncClient, db_session: Session):
    location_data_1 = LocationCreate(
        name="Duplicate Name Office Test",
        address_line1="1 First St Dup",
        city="Testville Dup",
        country="Testland Dup",
        organizationId=DEFAULT_ORG_ID
    )  
    response1 = await test_client.post("/api/v1/locations/", json=location_data_1.model_dump(mode='json'))
    assert response1.status_code == 201

    location_data_2 = LocationCreate(
        name="Duplicate Name Office Test",
        address_line1="2 Second St Dup",
        city="Testville Dup",
        country="Testland Dup",
        organizationId=DEFAULT_ORG_ID
    )
    response2 = await test_client.post("/api/v1/locations/", json=location_data_2.model_dump(mode='json'))
    assert response2.status_code == 400
    assert f"Location with name '{location_data_2.name}' already exists in this organization." in response2.json()["detail"]
