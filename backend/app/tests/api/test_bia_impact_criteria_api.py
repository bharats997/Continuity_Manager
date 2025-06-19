# backend/app/tests/api/test_bia_impact_criteria_api.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from uuid import uuid4, UUID

from app.schemas.bia_impact_criteria import (
    BIAImpactCriterionCreate, BIAImpactCriterionLevelCreate, BIAImpactCriterionResponse,
    BIAImpactCriterionUpdate, BIAImpactCriterionLevelUpdate
)
from app.models.domain.bia_impact_criteria import RatingTypeEnum
from app.models.domain.users import User
from app.models.domain.organizations import Organization
from app.models.domain.bia_categories import BIACategory

# Permissions (assuming these are defined in your RBAC setup)
BIA_IMPACT_CRITERIA_CREATE = "bia_impact_criteria:create"
BIA_IMPACT_CRITERIA_READ = "bia_impact_criteria:read"
BIA_IMPACT_CRITERIA_UPDATE = "bia_impact_criteria:update"
BIA_IMPACT_CRITERIA_DELETE = "bia_impact_criteria:delete"
BIA_IMPACT_CRITERIA_LIST = "bia_impact_criteria:list"

API_BASE_URL = "/api/v1/bia-impact-criteria/"

@pytest.mark.asyncio
class TestBIAImpactCriteriaAPI:
    async def test_create_bia_impact_criterion_success(
        self,
        async_client: AsyncClient,
        test_user_with_bia_create_permission: User, # Assumes a fixture providing user with CREATE perm
        test_bia_category: BIACategory,
        access_token_for_user_with_bia_create_permissions: str # Assumes fixture for token
    ):
        criterion_name = f"API Test Criterion {uuid4()}"
        level1 = BIAImpactCriterionLevelCreate(level_name="Low Impact", score=10, sequence_order=0)
        level2 = BIAImpactCriterionLevelCreate(level_name="Medium Impact", score=50, sequence_order=1)
        criterion_data = BIAImpactCriterionCreate(
            name=criterion_name,
            description="A criterion created via API test",
            rating_type=RatingTypeEnum.QUALITATIVE,
            bia_category_id=test_bia_category.id,
            levels=[
                BIAImpactCriterionLevelCreate(level_name="Low Impact", score=10, sequence_order=1),
                BIAImpactCriterionLevelCreate(level_name="Medium Impact", score=50, sequence_order=2)
            ]
        )

        response = await async_client.post(
            API_BASE_URL,
            headers={"Authorization": f"Bearer {access_token_for_user_with_bia_create_permissions}"},
            json=criterion_data.model_dump(mode='json')
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data["name"] == criterion_name
        assert response_data["bia_category_id"] == str(test_bia_category.id)
        assert response_data["organization_id"] == str(test_user_with_bia_create_permission.organization_id)
        assert len(response_data["levels"]) == 2
        assert response_data["levels"][0]["level_name"] == "Low Impact"

    async def test_create_bia_impact_criterion_no_permission(
        self,
        async_client: AsyncClient,
        test_user_without_bia_create_permission: User, # Assumes a fixture for user without CREATE perm
        test_bia_category: BIACategory,
        access_token_for_user_without_bia_create_permissions: str # Assumes fixture for token
    ):
        criterion_name = f"API Test Criterion NoPerm {uuid4()}"
        criterion_data = BIAImpactCriterionCreate(
            name=criterion_name,
            description="A criterion created via API test - no perm",
            rating_type=RatingTypeEnum.QUALITATIVE,
            bia_category_id=test_bia_category.id,
            levels=[BIAImpactCriterionLevelCreate(level_name="N/A", score=0, sequence_order=1)]
        )

        response = await async_client.post(
            API_BASE_URL,
            headers={"Authorization": f"Bearer {access_token_for_user_without_bia_create_permissions}"},
            json=criterion_data.model_dump(mode='json')
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_create_bia_impact_criterion_duplicate_name(
        self,
        async_client: AsyncClient,
        test_user_with_bia_create_permission: User,
        test_bia_category: BIACategory,
        access_token_for_user_with_bia_create_permissions: str,
        async_db_session: AsyncSession # To pre-populate
    ):
        # First, create one successfully
        criterion_name = f"API Test Criterion Dupe {uuid4()}"
        level_data = [BIAImpactCriterionLevelCreate(level_name="L1", score=1, sequence_order=1)]
        criterion_data_1 = BIAImpactCriterionCreate(
            name=criterion_name,
            description="First instance",
            rating_type=RatingTypeEnum.QUALITATIVE,
            bia_category_id=test_bia_category.id,
            levels=level_data
        )
        response1 = await async_client.post(
            API_BASE_URL + "/",
            headers={"Authorization": f"Bearer {access_token_for_user_with_bia_create_permissions}"},
            json=criterion_data_1.model_dump(mode='json')
        )
        assert response1.status_code == status.HTTP_201_CREATED

        # Then, attempt to create another with the same name and category
        criterion_data_2 = BIAImpactCriterionCreate(
            name=criterion_name, # Same name
            description="Second instance (duplicate)",
            rating_type=RatingTypeEnum.QUALITATIVE,
            bia_category_id=test_bia_category.id, # Same category
            levels=[BIAImpactCriterionLevelCreate(level_name="L2", score=2, sequence_order=2)]
        )
        response2 = await async_client.post(
            API_BASE_URL + "/",
            headers={"Authorization": f"Bearer {access_token_for_user_with_bia_create_permissions}"},
            json=criterion_data_2.model_dump(mode='json')
        )
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert f"BIA Impact Criterion with name '{criterion_name}' already exists for this BIA Category." in response2.json()["detail"]


    # --- Placeholder tests for other endpoints ---
    async def test_get_bia_impact_criterion_by_id_success(
        self, 
        async_client: AsyncClient, 
        test_user_with_bia_create_permission: User,
        access_token_for_user_with_bia_create_permissions: str, # For creation
        access_token_for_user_with_bia_read_permission: str,    # For reading
        test_bia_category: BIACategory
    ):
        # 1. Create a criterion first
        criterion_name = f"API Get Test Criterion {uuid4()}"
        level1 = BIAImpactCriterionLevelCreate(level_name="Critical", score=100, sequence_order=1)
        criterion_data_in = BIAImpactCriterionCreate(
            name=criterion_name,
            description="Test for API GET by ID",
            rating_type=RatingTypeEnum.QUALITATIVE,
            bia_category_id=test_bia_category.id,
            levels=[level1]
        )
        response_create = await async_client.post(
            API_BASE_URL,
            headers={"Authorization": f"Bearer {access_token_for_user_with_bia_create_permissions}"},
            json=criterion_data_in.model_dump(mode='json')
        )
        assert response_create.status_code == status.HTTP_201_CREATED
        created_criterion_data = response_create.json()
        criterion_id = created_criterion_data["id"]

        # 2. Get the criterion by ID
        response_get = await async_client.get(
            f"{API_BASE_URL}/{criterion_id}",
            headers={"Authorization": f"Bearer {access_token_for_user_with_bia_read_permission}"}
        )
        
        # 3. Assert success and data match
        assert response_get.status_code == status.HTTP_200_OK
        retrieved_criterion_data = response_get.json()
        assert retrieved_criterion_data["id"] == criterion_id
        assert retrieved_criterion_data["name"] == criterion_name
        assert retrieved_criterion_data["bia_category_id"] == str(test_bia_category.id)
        assert retrieved_criterion_data["organization_id"] == str(test_user_with_bia_create_permission.organization_id)
        assert len(retrieved_criterion_data["levels"]) == 1
        assert retrieved_criterion_data["levels"][0]["level_name"] == "Critical"

    async def test_get_bia_impact_criterion_by_id_not_found(self, async_client: AsyncClient, access_token_for_user_with_bia_read_permission: str):
        response = await async_client.get(
            f"{API_BASE_URL}/{uuid4()}",
            headers={"Authorization": f"Bearer {access_token_for_user_with_bia_read_permission}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_list_bia_impact_criteria_success(
        self, 
        async_client: AsyncClient, 
        test_user_with_bia_create_permission: User, # For org_id reference
        access_token_for_user_with_bia_create_permissions: str, # For creation
        access_token_for_user_with_bia_list_permission: str,    # For listing
        test_bia_category: BIACategory
    ):
        headers_create = {"Authorization": f"Bearer {access_token_for_user_with_bia_create_permissions}"}
        headers_list = {"Authorization": f"Bearer {access_token_for_user_with_bia_list_permission}"}
        org_id_str = str(test_user_with_bia_create_permission.organization_id)

        # 1. Create a couple of criteria
        crit1_name = f"API List Crit 1 {uuid4()}"
        crit1_data_in = BIAImpactCriterionCreate(
            name=crit1_name, 
            description="First criterion for listing", 
            rating_type=RatingTypeEnum.QUALITATIVE,
            bia_category_id=test_bia_category.id, 
            levels=[BIAImpactCriterionLevelCreate(level_name="L1C1", score=1, sequence_order=1)]
        )
        resp_create1 = await async_client.post(API_BASE_URL, headers=headers_create, json=crit1_data_in.model_dump(mode='json'))
        assert resp_create1.status_code == status.HTTP_201_CREATED
        crit1_id = resp_create1.json()["id"]

        crit2_name = f"API List Crit 2 {uuid4()}"
        crit2_data_in = BIAImpactCriterionCreate(
            name=crit2_name, 
            description="Second criterion for listing", 
            rating_type=RatingTypeEnum.QUALITATIVE,
            bia_category_id=test_bia_category.id, 
            levels=[BIAImpactCriterionLevelCreate(level_name="L1C2", score=2, sequence_order=2)]
        )
        resp_create2 = await async_client.post(API_BASE_URL, headers=headers_create, json=crit2_data_in.model_dump(mode='json'))
        assert resp_create2.status_code == status.HTTP_201_CREATED
        crit2_id = resp_create2.json()["id"]

        # 2. List criteria (default pagination)
        response_list_default = await async_client.get(API_BASE_URL, headers=headers_list)
        assert response_list_default.status_code == status.HTTP_200_OK
        list_data_default = response_list_default.json()
        
        assert list_data_default["total"] >= 2 # Could be more if other tests ran and didn't clean up, or other data exists
        assert len(list_data_default["results"]) >= 2
        
        # Filter to find our created items, as other tests might create data
        found_crit1 = any(item["id"] == crit1_id for item in list_data_default["results"])
        found_crit2 = any(item["id"] == crit2_id for item in list_data_default["results"])
        assert found_crit1, f"Criterion {crit1_id} not found in default list"
        assert found_crit2, f"Criterion {crit2_id} not found in default list"

        # 3. Test pagination: page 1, size 1
        response_p1_s1 = await async_client.get(f"{API_BASE_URL}?page=1&size=1", headers=headers_list)
        assert response_p1_s1.status_code == status.HTTP_200_OK
        data_p1_s1 = response_p1_s1.json()
        assert data_p1_s1["total"] >= 2
        assert len(data_p1_s1["results"]) == 1
        assert data_p1_s1["page"] == 1
        assert data_p1_s1["size"] == 1
        item_p1_s1_id = data_p1_s1["results"][0]["id"]

        # 4. Test pagination: page 2, size 1
        response_p2_s1 = await async_client.get(f"{API_BASE_URL}?page=2&size=1", headers=headers_list)
        assert response_p2_s1.status_code == status.HTTP_200_OK
        data_p2_s1 = response_p2_s1.json()
        assert data_p2_s1["total"] >= 2
        assert len(data_p2_s1["results"]) == 1
        assert data_p2_s1["page"] == 2
        assert data_p2_s1["size"] == 1
        item_p2_s1_id = data_p2_s1["results"][0]["id"]

        # Ensure items from page 1 and page 2 (size 1) are different if total is at least 2
        if data_p1_s1["total"] >= 2:
            assert item_p1_s1_id != item_p2_s1_id
            # Check if the two items we fetched via pagination are the ones we created
            # This assumes a consistent ordering or that they are the only two items.
            # For more robust test, might need to sort or be more specific if order is not guaranteed.
            paginated_ids = {item_p1_s1_id, item_p2_s1_id}
            # This assertion is tricky if other data exists. We'll assume for now that 
            # if we get two distinct items, and our two items are in the full list, it's likely working.
            # A more robust check would be to ensure that crit1_id and crit2_id are among the first N items
            # based on the default sort order of the API, if known.
            assert crit1_id in paginated_ids or crit2_id in paginated_ids

        # Test fetching with a page beyond the total items (approximate)
        # This assumes the default page size is e.g. 20. If we have 2 items, page 3 of size 1 should be empty.
        # If total is large, this might not be empty. A better way is to calculate last page.
        last_page_approx = (data_p1_s1["total"] // 1) + 1 # page after last if size is 1
        response_empty_page = await async_client.get(f"{API_BASE_URL}?page={last_page_approx}&size=1", headers=headers_list)
        assert response_empty_page.status_code == status.HTTP_200_OK
        data_empty_page = response_empty_page.json()
        assert data_empty_page["total"] == list_data_default["total"]
        assert len(data_empty_page["results"]) == 0
        assert data_empty_page["page"] == last_page_approx

    async def test_update_bia_impact_criterion_success(
        self, 
        async_client: AsyncClient, 
        test_user_with_bia_create_permission: User, # For org_id reference
        access_token_for_user_with_bia_create_permissions: str, # For creation
        access_token_for_user_with_bia_update_permission: str,    # For updating
        access_token_for_user_with_bia_read_permission: str,      # For re-fetching
        test_bia_category: BIACategory
    ):
        headers_create = {"Authorization": f"Bearer {access_token_for_user_with_bia_create_permissions}"}
        headers_update = {"Authorization": f"Bearer {access_token_for_user_with_bia_update_permission}"}
        headers_read = {"Authorization": f"Bearer {access_token_for_user_with_bia_read_permission}"}
        org_id_str = str(test_user_with_bia_create_permission.organization_id)

        # 1. Create initial criterion
        initial_name = f"API Initial Update Crit {uuid4()}"
        initial_levels = [BIAImpactCriterionLevelCreate(level_name="Original Level", score=5, sequence_order=1)]
        crit_create_data = BIAImpactCriterionCreate(
            name=initial_name, 
            description="Initial for update", 
            rating_type=RatingTypeEnum.QUALITATIVE,
            bia_category_id=test_bia_category.id, 
            levels=initial_levels
        )
        resp_create = await async_client.post(API_BASE_URL, headers=headers_create, json=crit_create_data.model_dump(mode='json'))
        assert resp_create.status_code == status.HTTP_201_CREATED
        created_crit_id = resp_create.json()["id"]

        # 2. Prepare update data
        updated_name = f"API Updated Crit {uuid4()}"
        updated_description = "Description has been updated"
        updated_levels = [
            BIAImpactCriterionLevelUpdate(level_name="Updated Level A", score=10, sequence_order=1),
            BIAImpactCriterionLevelUpdate(level_name="Updated Level B", score=20, sequence_order=2)
        ]
        crit_update_data = BIAImpactCriterionUpdate(
            name=updated_name, 
            description=updated_description, 
            levels=updated_levels
        )

        # 3. Call PUT to update
        resp_update = await async_client.put(
            f"{API_BASE_URL}/{created_crit_id}", 
            headers=headers_update, 
            json=crit_update_data.model_dump(mode='json', exclude_none=True) # exclude_none for partial updates if schema supports
        )
        assert resp_update.status_code == status.HTTP_200_OK
        updated_data_from_put = resp_update.json()

        # 4. Assert response from PUT reflects updates
        assert updated_data_from_put["id"] == created_crit_id
        assert updated_data_from_put["name"] == updated_name
        assert updated_data_from_put["description"] == updated_description
        assert len(updated_data_from_put["levels"]) == 2
        put_level_names_scores = {(l["level_name"], l["score"]) for l in updated_data_from_put["levels"]}
        assert ("Updated Level A", 10) in put_level_names_scores
        assert ("Updated Level B", 20) in put_level_names_scores

        # 5. Fetch again via GET and verify persisted changes
        resp_get = await async_client.get(f"{API_BASE_URL}/{created_crit_id}", headers=headers_read)
        assert resp_get.status_code == status.HTTP_200_OK
        fetched_data = resp_get.json()
        assert fetched_data["name"] == updated_name
        assert fetched_data["description"] == updated_description
        assert len(fetched_data["levels"]) == 2
        get_level_names_scores = {(l["level_name"], l["score"]) for l in fetched_data["levels"]}
        assert ("Updated Level A", 10) in get_level_names_scores
        assert ("Updated Level B", 20) in get_level_names_scores

    async def test_delete_bia_impact_criterion_success(
        self, 
        async_client: AsyncClient, 
        access_token_for_user_with_bia_create_permissions: str, # For creation
        access_token_for_user_with_bia_delete_permission: str,    # For deleting
        access_token_for_user_with_bia_read_permission: str,      # For re-fetching check
        test_bia_category: BIACategory
    ):
        headers_create = {"Authorization": f"Bearer {access_token_for_user_with_bia_create_permissions}"}
        headers_delete = {"Authorization": f"Bearer {access_token_for_user_with_bia_delete_permission}"}
        headers_read = {"Authorization": f"Bearer {access_token_for_user_with_bia_read_permission}"}

        # 1. Create a criterion
        criterion_name = f"API Delete Test Crit {uuid4()}"
        crit_create_data = BIAImpactCriterionCreate(
            name=criterion_name, 
            description="To be deleted via API", 
            rating_type=RatingTypeEnum.QUALITATIVE,
            bia_category_id=test_bia_category.id, 
            levels=[BIAImpactCriterionLevelCreate(level_name="Temp Level", score=1, sequence_order=1)]
        )
        resp_create = await async_client.post(API_BASE_URL, headers=headers_create, json=crit_create_data.model_dump(mode='json'))
        assert resp_create.status_code == status.HTTP_201_CREATED
        created_crit_id = resp_create.json()["id"]
        assert created_crit_id is not None

        # 2. Delete the criterion
        resp_delete = await async_client.delete(f"{API_BASE_URL}{created_crit_id}", headers=headers_delete) # Note: API_BASE_URL now has trailing slash
        
        # 3. Assert deletion success (router returns 204 No Content)
        assert resp_delete.status_code == status.HTTP_204_NO_CONTENT

        # 4. Attempt to GET the deleted criterion and assert 404 Not Found
        resp_get_deleted = await async_client.get(f"{API_BASE_URL}/{created_crit_id}", headers=headers_read)
        assert resp_get_deleted.status_code == status.HTTP_404_NOT_FOUND
