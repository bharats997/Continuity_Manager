import uuid
from typing import List, Optional, AsyncGenerator, Callable, Awaitable

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

# App specific imports
from app.models.domain.organizations import Organization as OrganizationModel
from app.models.domain.users import User as UserModel
from app.models.domain.roles import Role as RoleModel
from app.models.domain.bia_categories import BIACategory as BIACategoryModel
from app.main import app # For dependency cleanup

from app.schemas.bia_categories import (
    BIACategoryCreate,
    BIACategoryRead,
    BIACategoryUpdate,
)

# Import test helpers
from app.tests.helpers import (
    DEFAULT_ORG_ID,
    create_role_with_permissions_async,
    create_user_with_roles_async,
)



# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio



# --- Test Data Helper ---
def get_bia_category_create_payload(name: Optional[str] = None, description: Optional[str] = None, organization_id: Optional[uuid.UUID] = DEFAULT_ORG_ID) -> dict:
    payload = {
        "name": name if name is not None else f"Test BIA Category {uuid.uuid4().hex[:10]}",
        "description": description if description is not None else "A test BIA category description.",
        "organization_id": str(organization_id) if organization_id else str(DEFAULT_ORG_ID)
    }
    return {k: v for k, v in payload.items() if v is not None}


# --- BIA Category API Test Cases ---

# POST /bia-categories/
async def test_create_bia_category_as_bcm_manager(
    bcm_manager_bia_category_client: AsyncClient, 
    async_db_session: AsyncSession # Added async_db_session for DB verification
):
    payload = get_bia_category_create_payload()
    response = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert data["organization_id"] == payload["organization_id"]
    assert data["is_active"] is True
    assert "id" in data

    # Verify in DB
    category_in_db = await async_db_session.get(BIACategoryModel, uuid.UUID(data["id"]))
    assert category_in_db is not None
    assert category_in_db.name == payload["name"]

async def test_create_bia_category_as_ciso(
    ciso_bia_category_client: AsyncClient, 
    async_db_session: AsyncSession # Added for consistency, though not strictly needed if not verifying DB
):
    payload = get_bia_category_create_payload(name=f"CISO Created Category {uuid.uuid4().hex[:6]}")
    response = await ciso_bia_category_client.post("/api/v1/bia-categories/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == payload["name"]

async def test_create_bia_category_as_read_only_user_forbidden(
    read_only_bia_category_client: AsyncClient
):
    payload = get_bia_category_create_payload()
    response = await read_only_bia_category_client.post("/api/v1/bia-categories/", json=payload, expect_error=True)
    assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_create_bia_category_as_no_permission_user_forbidden(
    no_bia_category_permissions_client: AsyncClient
):
    payload = get_bia_category_create_payload()
    response = await no_bia_category_permissions_client.post("/api/v1/bia-categories/", json=payload, expect_error=True)
    assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_create_bia_category_duplicate_name_for_same_org_conflict(
    bcm_manager_bia_category_client: AsyncClient
):
    payload = get_bia_category_create_payload(name="Unique Name for Conflict Test")
    response1 = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload)
    assert response1.status_code == status.HTTP_201_CREATED

    response2 = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload, expect_error=True) # Same payload
    assert response2.status_code == status.HTTP_409_CONFLICT

async def test_create_bia_category_duplicate_name_for_different_org_allowed(
    bcm_manager_bia_category_client: AsyncClient, 
    async_db_session: AsyncSession
):
    org2_id = uuid.uuid4()
    # Ensure the new organization exists in the DB
    org2 = OrganizationModel(id=str(org2_id), name="Another Org for BIA Test") # Ensure UUID is string
    async_db_session.add(org2)
    await async_db_session.commit() # Commit to make it available

    payload1 = get_bia_category_create_payload(name="Shared Name Test", organization_id=DEFAULT_ORG_ID)
    response1 = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload1)
    assert response1.status_code == status.HTTP_201_CREATED
    
    # This part assumes the user (bcm_manager_bia_category_client) has rights to create for org2_id,
    # or the API allows specifying organization_id in payload and it's honored.
    # If the user is tied to DEFAULT_ORG_ID and cannot create for others, this needs a superadmin client.
    # For now, assuming the API allows it if specified in payload.
    payload2 = get_bia_category_create_payload(name="Shared Name Test", organization_id=org2_id)
    response2 = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload2)
    assert response2.status_code == status.HTTP_201_CREATED 
    data1 = response1.json()
    data2 = response2.json()
    assert data1["name"] == data2["name"]
    assert data1["organization_id"] != data2["organization_id"]
    assert data2["organization_id"] == str(org2_id)

async def test_create_bia_category_missing_name(bcm_manager_bia_category_client: AsyncClient):
    payload = get_bia_category_create_payload()
    del payload["name"]
    response = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload, expect_error=True)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_bia_category_empty_name(bcm_manager_bia_category_client: AsyncClient):
    payload = get_bia_category_create_payload(name="")
    response = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload, expect_error=True)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_bia_category_name_too_long(bcm_manager_bia_category_client: AsyncClient):
    payload = get_bia_category_create_payload(name="a" * 256) # Assuming max_length is 255
    response = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload, expect_error=True)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_bia_category_description_too_long(bcm_manager_bia_category_client: AsyncClient):
    payload = get_bia_category_create_payload(description="d" * 1001) # Assuming max_length is 1000
    response = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload, expect_error=True)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_bia_category_invalid_org_id_format(bcm_manager_bia_category_client: AsyncClient):
    payload = get_bia_category_create_payload()
    payload["organization_id"] = "not-a-uuid"
    response = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload, expect_error=True)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# GET /bia-categories/
async def test_list_bia_categories_as_bcm_manager(
    bcm_manager_bia_category_client: AsyncClient,
    async_db_session: AsyncSession # To ensure data is queryable
):
    # Create a couple of categories for the default org
    payload1 = get_bia_category_create_payload(name="BIA Cat List 1", organization_id=DEFAULT_ORG_ID)
    await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload1)
    payload2 = get_bia_category_create_payload(name="BIA Cat List 2", organization_id=DEFAULT_ORG_ID)
    await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload2)

    response = await bcm_manager_bia_category_client.get("/api/v1/bia-categories/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # Ensure we see at least the categories we created
    found_names = {item['name'] for item in data if item['organization_id'] == str(DEFAULT_ORG_ID)}
    assert payload1['name'] in found_names
    assert payload2['name'] in found_names
    for item in data: # Check all items returned belong to the user's org if org filtering is applied by default
        if item['organization_id'] == str(DEFAULT_ORG_ID): # Only check items from the default org
             assert item['organization_id'] == str(DEFAULT_ORG_ID)


async def test_list_bia_categories_as_ciso(
    ciso_bia_category_client: AsyncClient,
    async_db_session: AsyncSession 
):
    payload = get_bia_category_create_payload(name="BIA Cat for CISO List", organization_id=DEFAULT_ORG_ID)
    await ciso_bia_category_client.post("/api/v1/bia-categories/", json=payload)

    response = await ciso_bia_category_client.get("/api/v1/bia-categories/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert any(item['name'] == payload['name'] and item['organization_id'] == str(DEFAULT_ORG_ID) for item in data)

async def test_list_bia_categories_as_read_only_user(
    read_only_bia_category_client: AsyncClient,
    bcm_manager_bia_category_client: AsyncClient # To create data
):
    payload = get_bia_category_create_payload(name="BIA Cat for ReadOnly List", organization_id=DEFAULT_ORG_ID)
    await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload) 

    response = await read_only_bia_category_client.get("/api/v1/bia-categories/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert any(item['name'] == payload['name'] and item['organization_id'] == str(DEFAULT_ORG_ID) for item in data)

async def test_list_bia_categories_as_no_permission_user_forbidden(
    no_bia_category_permissions_client: AsyncClient
):
    response = await no_bia_category_permissions_client.get("/api/v1/bia-categories/", expect_error=True)
    assert response.status_code == status.HTTP_403_FORBIDDEN

# GET /bia-categories/{category_id}
async def test_get_bia_category_by_id_as_bcm_manager(
    bcm_manager_bia_category_client: AsyncClient
):
    payload = get_bia_category_create_payload(name="BIA Cat Get By ID")
    create_response = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload)
    assert create_response.status_code == status.HTTP_201_CREATED
    category_id = create_response.json()["id"]

    response = await bcm_manager_bia_category_client.get(f"/api/v1/bia-categories/{category_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == category_id
    assert data["name"] == payload["name"]
    assert data["organization_id"] == str(DEFAULT_ORG_ID)

async def test_get_bia_category_by_id_as_read_only_user(
    read_only_bia_category_client: AsyncClient,
    bcm_manager_bia_category_client: AsyncClient # To create data
):
    payload = get_bia_category_create_payload(name="BIA Cat Get By ID ReadOnly")
    create_response = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload)
    category_id = create_response.json()["id"]

    response = await read_only_bia_category_client.get(f"/api/v1/bia-categories/{category_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == category_id

async def test_get_bia_category_by_id_as_no_permission_user_forbidden(
    no_bia_category_permissions_client: AsyncClient,
    bcm_manager_bia_category_client: AsyncClient # To create data
):
    payload = get_bia_category_create_payload(name="BIA Cat Get By ID NoPerm")
    create_response = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload)
    category_id = create_response.json()["id"]

    response = await no_bia_category_permissions_client.get(f"/api/v1/bia-categories/{category_id}", expect_error=True)
    assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_get_bia_category_by_id_non_existent(bcm_manager_bia_category_client: AsyncClient):
    non_existent_id = uuid.uuid4()
    response = await bcm_manager_bia_category_client.get(f"/api/v1/bia-categories/{non_existent_id}", expect_error=True)
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_get_bia_category_by_id_from_different_org_forbidden(
    bcm_manager_bia_category_client: AsyncClient, # Belongs to DEFAULT_ORG_ID
    async_db_session: AsyncSession
):
    # Create a category in a different organization
    org2_id = uuid.uuid4()
    org2 = OrganizationModel(id=str(org2_id), name="Org2 for Get Test")
    async_db_session.add(org2)
    
    category_other_org = BIACategoryModel(
        name="Category in Org2", 
        organization_id=str(org2_id),
        description="Belongs to another org"
    )
    async_db_session.add(category_other_org)
    await async_db_session.commit()
    await async_db_session.refresh(category_other_org)
    
    category_id_other_org = category_other_org.id

    response = await bcm_manager_bia_category_client.get(f"/api/v1/bia-categories/{category_id_other_org}", expect_error=True)
    # This should be 404 if strict tenancy is applied (user can't even "see" it exists)
    # or 403 if they can see it but not access. 404 is more common for tenancy.
    assert response.status_code == status.HTTP_404_NOT_FOUND


# PUT /bia-categories/{category_id}
async def test_update_bia_category_as_bcm_manager(
    bcm_manager_bia_category_client: AsyncClient,
    async_db_session: AsyncSession
):
    payload = get_bia_category_create_payload(name="BIA Cat To Update")
    create_response = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload)
    category_id = create_response.json()["id"]

    update_payload = {"name": "Updated BIA Cat Name", "description": "Updated description."}
    response = await bcm_manager_bia_category_client.put(f"/api/v1/bia-categories/{category_id}", json=update_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == category_id
    assert data["name"] == update_payload["name"]
    assert data["description"] == update_payload["description"]
    assert data["organization_id"] == str(DEFAULT_ORG_ID) # Org ID should not change on update

    # Verify in DB
    category_in_db = await async_db_session.get(BIACategoryModel, uuid.UUID(category_id))
    assert category_in_db is not None
    assert category_in_db.name == update_payload["name"]

async def test_update_bia_category_as_read_only_user_forbidden(
    read_only_bia_category_client: AsyncClient,
    bcm_manager_bia_category_client: AsyncClient # To create data
):
    payload = get_bia_category_create_payload(name="BIA Cat Update ReadOnly Test")
    create_response = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload)
    category_id = create_response.json()["id"]

    update_payload = {"name": "Attempted Update"}
    response = await read_only_bia_category_client.put(f"/api/v1/bia-categories/{category_id}", json=update_payload, expect_error=True)
    assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_update_bia_category_non_existent(bcm_manager_bia_category_client: AsyncClient):
    non_existent_id = uuid.uuid4()
    update_payload = {"name": "Update Non Existent"}
    response = await bcm_manager_bia_category_client.put(f"/api/v1/bia-categories/{non_existent_id}", json=update_payload, expect_error=True)
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_update_bia_category_to_duplicate_name_conflict(
    bcm_manager_bia_category_client: AsyncClient
):
    cat1_payload = get_bia_category_create_payload(name="BIA Cat Original Name 1")
    cat1_res = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=cat1_payload)
    
    cat2_payload = get_bia_category_create_payload(name="BIA Cat To Be Updated To Duplicate")
    cat2_res = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=cat2_payload)
    cat2_id = cat2_res.json()["id"]

    update_payload = {"name": cat1_payload["name"]} # Try to update cat2 to cat1's name
    response = await bcm_manager_bia_category_client.put(f"/api/v1/bia-categories/{cat2_id}", json=update_payload, expect_error=True)
    assert response.status_code == status.HTTP_409_CONFLICT

# DELETE /bia-categories/{category_id}
async def test_delete_bia_category_as_bcm_manager(
    bcm_manager_bia_category_client: AsyncClient,
    async_db_session: AsyncSession
):
    payload = get_bia_category_create_payload(name="BIA Cat To Delete")
    create_response = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload)
    category_id = create_response.json()["id"]

    response = await bcm_manager_bia_category_client.delete(f"/api/v1/bia-categories/{category_id}")
    assert response.status_code == status.HTTP_200_OK # Or 204 if no content
    data = response.json() # Assuming 200 OK with deleted object returned
    assert data["id"] == category_id
    assert data["name"] == payload["name"] 
    # Optionally, check is_active is False if soft delete, or row is gone if hard delete
    # For soft delete:
    # assert data["is_active"] is False 
    # category_in_db = await async_db_session.get(BIACategoryModel, uuid.UUID(category_id))
    # assert category_in_db is not None
    # assert category_in_db.is_active is False
    
    # For hard delete (current assumption based on typical delete returning object):
    category_in_db = await async_db_session.get(BIACategoryModel, uuid.UUID(category_id))
    assert category_in_db is None # Or check for soft delete flag

async def test_delete_bia_category_as_read_only_user_forbidden(
    read_only_bia_category_client: AsyncClient,
    bcm_manager_bia_category_client: AsyncClient # To create data
):
    payload = get_bia_category_create_payload(name="BIA Cat Delete ReadOnly Test")
    create_response = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload)
    category_id = create_response.json()["id"]

    response = await read_only_bia_category_client.delete(f"/api/v1/bia-categories/{category_id}", expect_error=True)
    assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_delete_bia_category_non_existent(bcm_manager_bia_category_client: AsyncClient):
    non_existent_id = uuid.uuid4()
    response = await bcm_manager_bia_category_client.delete(f"/api/v1/bia-categories/{non_existent_id}", expect_error=True)
    assert response.status_code == status.HTTP_404_NOT_FOUND

# --- Test is_active flag behavior (if applicable) ---

async def test_create_bia_category_is_active_defaults_true(bcm_manager_bia_category_client: AsyncClient):
    payload = get_bia_category_create_payload(name="BIA Cat Active Default")
    # Do not specify is_active in payload
    response = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["is_active"] is True

async def test_update_bia_category_can_set_inactive(
    bcm_manager_bia_category_client: AsyncClient,
    async_db_session: AsyncSession
):
    payload = get_bia_category_create_payload(name="BIA Cat Set Inactive")
    create_response = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload)
    category_id = create_response.json()["id"]

    update_payload = {"is_active": False}
    response = await bcm_manager_bia_category_client.put(f"/api/v1/bia-categories/{category_id}", json=update_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_active"] is False

    category_in_db = await async_db_session.get(BIACategoryModel, uuid.UUID(category_id))
    assert category_in_db is not None
    assert category_in_db.is_active is False

async def test_get_inactive_bia_category_by_id(
    bcm_manager_bia_category_client: AsyncClient,
    async_db_session: AsyncSession
):
    # Create and set inactive
    payload = get_bia_category_create_payload(name="BIA Cat Get Inactive")
    create_res = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=payload)
    category_id = create_res.json()["id"]
    await bcm_manager_bia_category_client.put(f"/api/v1/bia-categories/{category_id}", json={"is_active": False})

    response = await bcm_manager_bia_category_client.get(f"/api/v1/bia-categories/{category_id}")
    # Behavior for GET on inactive items can vary:
    # 1. Still returns 200 OK with is_active: false
    # 2. Returns 404 Not Found (as if it doesn't exist for normal users)
    # Assuming 200 OK for now, as it's often useful for admins to see inactive items.
    assert response.status_code == status.HTTP_200_OK 
    data = response.json()
    assert data["id"] == category_id
    assert data["is_active"] is False

async def test_list_bia_categories_excludes_inactive_by_default(
    bcm_manager_bia_category_client: AsyncClient,
    async_db_session: AsyncSession
):
    active_name = "Active BIA Cat for List Filter"
    inactive_name = "Inactive BIA Cat for List Filter"

    # Create one active
    await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=get_bia_category_create_payload(name=active_name))
    
    # Create one and make it inactive
    inactive_res = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=get_bia_category_create_payload(name=inactive_name))
    inactive_id = inactive_res.json()["id"]
    await bcm_manager_bia_category_client.put(f"/api/v1/bia-categories/{inactive_id}", json={"is_active": False})

    response = await bcm_manager_bia_category_client.get("/api/v1/bia-categories/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    found_active = False
    found_inactive = False
    for item in data:
        if item["name"] == active_name:
            found_active = True
            assert item["is_active"] is True
        if item["name"] == inactive_name: # This should not be found if inactive are filtered
            found_inactive = True 
            
    assert found_active is True
    assert found_inactive is False # Default list should not include inactive items

async def test_list_bia_categories_can_include_inactive_with_param(
    bcm_manager_bia_category_client: AsyncClient,
    async_db_session: AsyncSession
):
    active_name = "Active BIA Cat for List Param"
    inactive_name = "Inactive BIA Cat for List Param"

    await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=get_bia_category_create_payload(name=active_name))
    inactive_res = await bcm_manager_bia_category_client.post("/api/v1/bia-categories/", json=get_bia_category_create_payload(name=inactive_name))
    inactive_id = inactive_res.json()["id"]
    await bcm_manager_bia_category_client.put(f"/api/v1/bia-categories/{inactive_id}", json={"is_active": False})

    response = await bcm_manager_bia_category_client.get("/api/v1/bia-categories/?include_inactive=true")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    found_active = any(item["name"] == active_name and item["is_active"] is True for item in data)
    found_inactive = any(item["name"] == inactive_name and item["is_active"] is False for item in data)
            
    assert found_active is True
    assert found_inactive is True # With param, inactive should be included