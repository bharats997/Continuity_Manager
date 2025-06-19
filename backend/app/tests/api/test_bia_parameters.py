import pytest
from httpx import AsyncClient
from fastapi import status
from uuid import uuid4, UUID
from typing import Callable, Awaitable

from app.config import settings
from app.models.domain.users import User
from app.schemas.bia_parameters import BIAImpactScaleCreate, BIATimeframeCreate

# --- Constants ---
API_ENDPOINT_IMPACT_SCALES = f"{settings.API_V1_STR}/bia-parameters/impact-scales/"
API_ENDPOINT_TIMEFRAMES = f"{settings.API_V1_STR}/bia-parameters/timeframes/"

# --- BCM Manager: Full Access Tests (Happy Path) ---

@pytest.mark.asyncio
async def test_bcm_manager_can_create_read_update_delete_impact_scale(bcm_manager_user_authenticated_client: AsyncClient):
    """Tests that a BCM Manager has full CRUD access to BIA Impact Scales."""
    scale_name = f"Financial Scale - {uuid4()}"
    create_data = {"scale_name": scale_name, "levels": [{"name": "Low", "description": "Low financial impact."}]}
    
    # CREATE
    response = await bcm_manager_user_authenticated_client.post(API_ENDPOINT_IMPACT_SCALES, json=create_data)
    assert response.status_code == status.HTTP_201_CREATED
    created_scale = response.json()
    assert created_scale["scale_name"] == scale_name
    assert created_scale["levels"][0]["name"] == "Low"
    scale_id = created_scale["id"]

    # READ (Get by ID)
    response = await bcm_manager_user_authenticated_client.get(f"{API_ENDPOINT_IMPACT_SCALES}{scale_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["scale_name"] == scale_name

    # UPDATE
    updated_scale_name = f"Updated Financial Scale - {uuid4()}"
    update_data = {"scale_name": updated_scale_name}
    response = await bcm_manager_user_authenticated_client.put(f"{API_ENDPOINT_IMPACT_SCALES}{scale_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["scale_name"] == updated_scale_name

    # DELETE
    response = await bcm_manager_user_authenticated_client.delete(f"{API_ENDPOINT_IMPACT_SCALES}{scale_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # VERIFY DELETION (GET should now be 404)
    response = await bcm_manager_user_authenticated_client.get(f"{API_ENDPOINT_IMPACT_SCALES}{scale_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_bcm_manager_can_create_read_update_delete_timeframe(bcm_manager_user_authenticated_client: AsyncClient):
    """Tests that a BCM Manager has full CRUD access to BIA Timeframes."""
    timeframe_name = f"RTO 2h - {uuid4()}"
    create_data = {"timeframe_name": timeframe_name, "sequence_order": 2}

    # CREATE
    response = await bcm_manager_user_authenticated_client.post(API_ENDPOINT_TIMEFRAMES, json=create_data)
    assert response.status_code == status.HTTP_201_CREATED
    created_timeframe = response.json()
    assert created_timeframe["timeframe_name"] == timeframe_name
    timeframe_id = created_timeframe["id"]

    # READ (List)
    response = await bcm_manager_user_authenticated_client.get(API_ENDPOINT_TIMEFRAMES)
    assert response.status_code == status.HTTP_200_OK
    assert any(t["id"] == timeframe_id for t in response.json())

    # UPDATE
    updated_timeframe_name = f"Updated RTO 2h - {uuid4()}"
    update_data = {"timeframe_name": updated_timeframe_name, "sequence_order": 10}
    response = await bcm_manager_user_authenticated_client.put(f"{API_ENDPOINT_TIMEFRAMES}{timeframe_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["timeframe_name"] == updated_timeframe_name

    # DELETE
    response = await bcm_manager_user_authenticated_client.delete(f"{API_ENDPOINT_TIMEFRAMES}{timeframe_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

# --- Internal Auditor: Read-Only Access Tests ---

@pytest.mark.asyncio
async def test_internal_auditor_has_read_only_access(
    internal_auditor_user_authenticated_client: AsyncClient, 
    bcm_manager_user_authenticated_client: AsyncClient
):
    """Tests that an Internal Auditor has read-only access and is forbidden from CUD operations."""
    # 1. Create a resource with a permitted user (BCM Manager)
    scale_data = {"scale_name": f"Auditable Scale - {uuid4()}", "levels": []}
    scale_response = await bcm_manager_user_authenticated_client.post(API_ENDPOINT_IMPACT_SCALES, json=scale_data)
    scale_id = scale_response.json()["id"]

    # 2. Auditor should be able to READ (List and Get by ID)
    assert (await internal_auditor_user_authenticated_client.get(API_ENDPOINT_IMPACT_SCALES)).status_code == status.HTTP_200_OK
    assert (await internal_auditor_user_authenticated_client.get(f"{API_ENDPOINT_IMPACT_SCALES}{scale_id}")).status_code == status.HTTP_200_OK

    # 3. Auditor should be FORBIDDEN from CREATE, UPDATE, or DELETE
    create_attempt_data = {"scale_name": f"Auditor Create Attempt - {uuid4()}"}
    update_attempt_data = {"scale_name": "Auditor Update Attempt"}
    assert (await internal_auditor_user_authenticated_client.post(API_ENDPOINT_IMPACT_SCALES, json=create_attempt_data)).status_code == status.HTTP_403_FORBIDDEN
    assert (await internal_auditor_user_authenticated_client.put(f"{API_ENDPOINT_IMPACT_SCALES}{scale_id}", json=update_attempt_data)).status_code == status.HTTP_403_FORBIDDEN
    assert (await internal_auditor_user_authenticated_client.delete(f"{API_ENDPOINT_IMPACT_SCALES}{scale_id}")).status_code == status.HTTP_403_FORBIDDEN

# --- General User: No Access Tests ---

@pytest.mark.asyncio
async def test_general_user_is_denied_all_access(
    general_user_authenticated_client: AsyncClient, 
    bcm_manager_user_authenticated_client: AsyncClient
):
    """Tests that a user without specific BIA permissions is denied all access."""
    # 1. Create a resource with a permitted user
    scale_data = {"scale_name": f"Protected Scale - {uuid4()}", "levels": []}
    scale_response = await bcm_manager_user_authenticated_client.post(API_ENDPOINT_IMPACT_SCALES, json=scale_data)
    scale_id = scale_response.json()["id"]

    # 2. General user should be FORBIDDEN from all CRUD operations
    assert (await general_user_authenticated_client.get(API_ENDPOINT_IMPACT_SCALES)).status_code == status.HTTP_403_FORBIDDEN
    assert (await general_user_authenticated_client.get(f"{API_ENDPOINT_IMPACT_SCALES}{scale_id}")).status_code == status.HTTP_403_FORBIDDEN
    assert (await general_user_authenticated_client.post(API_ENDPOINT_IMPACT_SCALES, json=scale_data)).status_code == status.HTTP_403_FORBIDDEN
    assert (await general_user_authenticated_client.put(f"{API_ENDPOINT_IMPACT_SCALES}{scale_id}", json={})).status_code == status.HTTP_403_FORBIDDEN
    assert (await general_user_authenticated_client.delete(f"{API_ENDPOINT_IMPACT_SCALES}{scale_id}")).status_code == status.HTTP_403_FORBIDDEN

# --- Functional Tests (Uniqueness) ---

@pytest.mark.asyncio
async def test_create_impact_scale_with_duplicate_name_fails(bcm_manager_user_authenticated_client: AsyncClient):
    """Tests that creating an impact scale with a duplicate name within the same organization fails."""
    scale_name = f"Duplicate Scale Name Test - {uuid4()}"
    scale_data = BIAImpactScaleCreate(scale_name=scale_name, levels=[]).model_dump()
    
    response1 = await bcm_manager_user_authenticated_client.post(API_ENDPOINT_IMPACT_SCALES, json=scale_data)
    assert response1.status_code == status.HTTP_201_CREATED

    response2 = await bcm_manager_user_authenticated_client.post(API_ENDPOINT_IMPACT_SCALES, json=scale_data)
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response2.json()["detail"]

@pytest.mark.asyncio
async def test_create_timeframe_with_duplicate_name_fails(bcm_manager_user_authenticated_client: AsyncClient):
    """Tests that creating a timeframe with a duplicate name within the same organization fails."""
    timeframe_name = f"Duplicate Timeframe Name Test - {uuid4()}"
    timeframe_data = BIATimeframeCreate(timeframe_name=timeframe_name, sequence_order=1).model_dump()

    response1 = await bcm_manager_user_authenticated_client.post(API_ENDPOINT_TIMEFRAMES, json=timeframe_data)
    assert response1.status_code == status.HTTP_201_CREATED

    response2 = await bcm_manager_user_authenticated_client.post(API_ENDPOINT_TIMEFRAMES, json=timeframe_data)
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response2.json()["detail"]

# --- Multi-Tenancy / Cross-Organization Tests ---

@pytest.mark.asyncio
async def test_user_cannot_access_bia_parameters_from_another_organization(
    bcm_manager_user_async: User,
    async_client_authenticated_as_user_factory: Callable[[User, str, UUID], Awaitable[AsyncClient]]
):
    """Tests that a user cannot access or modify BIA parameters from a different organization."""
    # 1. Create a client for Org 1 and create a resource
    org1_id = bcm_manager_user_async.organization_id
    org1_client = await async_client_authenticated_as_user_factory(bcm_manager_user_async)
    scale_name = f"Org1 Scale - {uuid4()}"
    response = await org1_client.post(API_ENDPOINT_IMPACT_SCALES, json={"scale_name": scale_name, "levels": []})
    assert response.status_code == status.HTTP_201_CREATED
    org1_scale_id = response.json()["id"]

    # 2. Create a client for a user in Org 2
    org2_id = uuid4()
    org2_client = await async_client_authenticated_as_user_factory(
        user_identifier=f"org2_user_{uuid4()}@example.com",
        role_override="BCM_MANAGER",
        organization_id_override=org2_id
    )

    # 3. Assert that Org 2 user CANNOT access Org 1's resource
    # GET / LIST (should not see org1's scale)
    response = await org2_client.get(API_ENDPOINT_IMPACT_SCALES)
    assert response.status_code == status.HTTP_200_OK
    assert not any(item['id'] == org1_scale_id for item in response.json())

    # GET by ID (should be 404)
    response = await org2_client.get(f"{API_ENDPOINT_IMPACT_SCALES}{org1_scale_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # PUT (should be 404)
    response = await org2_client.put(f"{API_ENDPOINT_IMPACT_SCALES}{org1_scale_id}", json={"scale_name": "Attempted Update"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # DELETE (should be 404)
    response = await org2_client.delete(f"{API_ENDPOINT_IMPACT_SCALES}{org1_scale_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
