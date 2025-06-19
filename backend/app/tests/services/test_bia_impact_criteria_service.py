# backend/app/tests/services/test_bia_impact_criteria_service.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4, UUID

from app.services.bia_impact_criteria_service import BIAImpactCriteriaService
from app.schemas.bia_impact_criteria import (
    BIAImpactCriterionCreate, BIAImpactCriterionLevelCreate, BIAImpactCriterionUpdate
)
from app.models.domain.users import User
from app.models.domain.organizations import Organization
from app.models.domain.bia_categories import BIACategory
from app.core.exceptions import NotFoundException, BadRequestException

# Placeholder for test_user, test_organization, test_bia_category fixtures
# These would typically be defined in conftest.py or helpers.py

@pytest.mark.asyncio
class TestBIAImpactCriteriaService:
    @pytest.fixture
    async def service(self, async_db_session: AsyncSession) -> BIAImpactCriteriaService:
        return BIAImpactCriteriaService(db_session=async_db_session)

    async def test_create_criterion_with_levels(
        self, 
        service: BIAImpactCriteriaService, 
        async_db_session: AsyncSession, 
        test_user_with_bia_create_permission: User, 
        test_bia_category: BIACategory
    ):
        criterion_name = f"Test Criterion {uuid4()}"
        level1 = BIAImpactCriterionLevelCreate(level_name="Low", score=1)
        level2 = BIAImpactCriterionLevelCreate(level_name="Medium", score=5)
        criterion_in = BIAImpactCriterionCreate(
            name=criterion_name,
            description="Test description",
            bia_category_id=test_bia_category.id,
            levels=[level1, level2]
        )

        created_criterion = await service.create_criterion_with_levels(
            criterion_in=criterion_in,
            organization_id=test_user_with_bia_create_permission.organization_id,
            user_id=test_user_with_bia_create_permission.id
        )

        assert created_criterion is not None
        assert created_criterion.name == criterion_name
        assert created_criterion.organization_id == test_user_with_bia_create_permission.organization_id
        assert created_criterion.bia_category_id == test_bia_category.id
        assert created_criterion.created_by_id == test_user_with_bia_create_permission.id
        assert len(created_criterion.levels) == 2
        assert created_criterion.levels[0].level_name == "Low"
        assert created_criterion.levels[0].score == 1
        assert created_criterion.levels[1].level_name == "Medium"
        assert created_criterion.levels[1].score == 5

        # Verify in DB
        db_criterion = await service.get_criterion_by_id(
            criterion_id=created_criterion.id, 
            organization_id=test_user_with_bia_create_permission.organization_id
        )
        assert db_criterion is not None
        assert db_criterion.name == criterion_name
        assert len(db_criterion.levels) == 2

    async def test_create_criterion_duplicate_name_in_category(
        self, 
        service: BIAImpactCriteriaService, 
        async_db_session: AsyncSession, 
        test_user_with_bia_create_permission: User, 
        test_bia_category: BIACategory
    ):
        criterion_name = f"Unique Criterion Name {uuid4()}"
        criterion_in_1 = BIAImpactCriterionCreate(
            name=criterion_name,
            description="Test description 1",
            bia_category_id=test_bia_category.id,
            levels=[BIAImpactCriterionLevelCreate(level_name="L1", score=1)]
        )
        await service.create_criterion_with_levels(
            criterion_in=criterion_in_1,
            organization_id=test_user.organization_id,
            user_id=test_user.id
        )

        criterion_in_2 = BIAImpactCriterionCreate(
            name=criterion_name, # Same name
            description="Test description 2",
            bia_category_id=test_bia_category.id, # Same category
            levels=[BIAImpactCriterionLevelCreate(level_name="L2", score=2)]
        )
        with pytest.raises(BadRequestException) as excinfo:
            await service.create_criterion_with_levels(
                criterion_in=criterion_in_2,
                organization_id=test_user.organization_id,
                user_id=test_user.id
            )
        assert f"BIA Impact Criterion with name '{criterion_name}' already exists for this BIA Category." in str(excinfo.value)

    # Placeholder for other tests
    async def test_get_criterion_by_id(self, service: BIAImpactCriteriaService, test_user_with_bia_create_permission: User, test_bia_category: BIACategory):
        criterion_name = f"Test Get Criterion {uuid4()}"
        level_data = [BIAImpactCriterionLevelCreate(level_name="High", score=10)]
        criterion_in = BIAImpactCriterionCreate(
            name=criterion_name,
            description="Criterion for get_by_id test",
            bia_category_id=test_bia_category.id,
            levels=level_data
        )

        created_criterion = await service.create_criterion_with_levels(
            criterion_in=criterion_in,
            organization_id=test_user_with_bia_create_permission.organization_id,
            user_id=test_user_with_bia_create_permission.id
        )
        assert created_criterion is not None

        retrieved_criterion = await service.get_criterion_by_id(
            criterion_id=created_criterion.id,
            organization_id=test_user_with_bia_create_permission.organization_id
        )

        assert retrieved_criterion is not None
        assert retrieved_criterion.id == created_criterion.id
        assert retrieved_criterion.name == criterion_name
        assert retrieved_criterion.bia_category_id == test_bia_category.id
        assert len(retrieved_criterion.levels) == 1
        assert retrieved_criterion.levels[0].level_name == "High"

    async def test_get_criterion_by_id_not_found(self, service: BIAImpactCriteriaService, test_user_with_bia_create_permission: User):
        with pytest.raises(NotFoundException):
            await service.get_criterion_by_id(criterion_id=uuid4(), organization_id=test_user_with_bia_create_permission.organization_id)

    async def test_get_criteria_by_organization(self, service: BIAImpactCriteriaService, test_user_with_bia_create_permission: User, test_bia_category: BIACategory):
        org_id = test_user_with_bia_create_permission.organization_id
        user_id = test_user_with_bia_create_permission.id

        criterion1_name = f"Org Criterion 1 {uuid4()}"
        crit1_in = BIAImpactCriterionCreate(
            name=criterion1_name, bia_category_id=test_bia_category.id, levels=[BIAImpactCriterionLevelCreate(level_name="L1C1", score=1)]
        )
        crit1 = await service.create_criterion_with_levels(criterion_in=crit1_in, organization_id=org_id, user_id=user_id)

        criterion2_name = f"Org Criterion 2 {uuid4()}"
        crit2_in = BIAImpactCriterionCreate(
            name=criterion2_name, bia_category_id=test_bia_category.id, levels=[BIAImpactCriterionLevelCreate(level_name="L1C2", score=2)]
        )
        crit2 = await service.create_criterion_with_levels(criterion_in=crit2_in, organization_id=org_id, user_id=user_id)

        # Test fetching all (default page size should be large enough for 2)
        response = await service.get_criteria_by_organization(organization_id=org_id)
        assert response["total"] == 2
        assert len(response["results"]) == 2
        retrieved_ids = {str(c.id) for c in response["results"]}
        assert str(crit1.id) in retrieved_ids
        assert str(crit2.id) in retrieved_ids

        # Test pagination: page 1, size 1
        response_page1_size1 = await service.get_criteria_by_organization(organization_id=org_id, page=1, size=1)
        assert response_page1_size1["total"] == 2
        assert len(response_page1_size1["results"]) == 1
        assert response_page1_size1["page"] == 1
        assert response_page1_size1["size"] == 1

        # Test pagination: page 2, size 1
        response_page2_size1 = await service.get_criteria_by_organization(organization_id=org_id, page=2, size=1)
        assert response_page2_size1["total"] == 2
        assert len(response_page2_size1["results"]) == 1
        assert response_page2_size1["page"] == 2
        assert response_page2_size1["size"] == 1

        # Ensure items from page 1 and page 2 (size 1) are different and are the ones we created
        assert response_page1_size1["results"][0].id != response_page2_size1["results"][0].id
        page_retrieved_ids = {str(response_page1_size1["results"][0].id), str(response_page2_size1["results"][0].id)}
        assert str(crit1.id) in page_retrieved_ids
        assert str(crit2.id) in page_retrieved_ids

        # Test fetching with a page beyond the total items
        response_empty_page = await service.get_criteria_by_organization(organization_id=org_id, page=3, size=1)
        assert response_empty_page["total"] == 2
        assert len(response_empty_page["results"]) == 0
        assert response_empty_page["page"] == 3

    async def test_update_criterion_with_levels(self, service: BIAImpactCriteriaService, test_user_with_bia_create_permission: User, test_bia_category: BIACategory):
        org_id = test_user_with_bia_create_permission.organization_id
        user_id = test_user_with_bia_create_permission.id

        # 1. Create initial criterion
        initial_name = f"Initial Criterion {uuid4()}"
        initial_levels = [
            BIAImpactCriterionLevelCreate(level_name="Low", score=1),
            BIAImpactCriterionLevelCreate(level_name="Medium", score=5)
        ]
        criterion_in_create = BIAImpactCriterionCreate(
            name=initial_name,
            description="Initial description",
            bia_category_id=test_bia_category.id,
            levels=initial_levels
        )
        created_criterion = await service.create_criterion_with_levels(
            criterion_in=criterion_in_create, organization_id=org_id, user_id=user_id
        )
        assert created_criterion is not None
        assert len(created_criterion.levels) == 2

        # 2. Prepare update data
        updated_name = f"Updated Criterion {uuid4()}"
        updated_description = "Updated description"
        # Modify one level, remove one (implicitly, by not including it), add a new one
        updated_levels_in = [
            BIAImpactCriterionLevelUpdate(level_name="Slightly Low", score=2), # Modifies "Low"
            BIAImpactCriterionLevelUpdate(level_name="High", score=10)      # New level
        ]
        criterion_in_update = BIAImpactCriterionUpdate(
            name=updated_name,
            description=updated_description,
            levels=updated_levels_in
        )

        # 3. Call update service method
        updated_criterion = await service.update_criterion_with_levels(
            criterion_id=created_criterion.id,
            obj_in=criterion_in_update,
            organization_id=org_id,
            updated_by_id=user_id
        )

        # 4. Assert returned criterion reflects updates
        assert updated_criterion is not None
        assert updated_criterion.id == created_criterion.id
        assert updated_criterion.name == updated_name
        assert updated_criterion.description == updated_description
        assert updated_criterion.updated_by_id == user_id
        assert len(updated_criterion.levels) == 2
        
        level_names_scores = {(l.level_name, l.score) for l in updated_criterion.levels}
        assert ("Slightly Low", 2) in level_names_scores
        assert ("High", 10) in level_names_scores

        # 5. Fetch again and assert persisted changes
        refetched_criterion = await service.get_criterion_by_id(
            criterion_id=created_criterion.id, organization_id=org_id
        )
        assert refetched_criterion is not None
        assert refetched_criterion.name == updated_name
        assert refetched_criterion.description == updated_description
        assert len(refetched_criterion.levels) == 2
        refetched_level_names_scores = {(l.level_name, l.score) for l in refetched_criterion.levels}
        assert ("Slightly Low", 2) in refetched_level_names_scores
        assert ("High", 10) in refetched_level_names_scores

    async def test_delete_criterion(self, service: BIAImpactCriteriaService, test_user_with_bia_create_permission: User, test_bia_category: BIACategory):
        org_id = test_user_with_bia_create_permission.organization_id
        user_id = test_user_with_bia_create_permission.id

        # 1. Create a criterion
        criterion_name = f"Criterion to Delete {uuid4()}"
        criterion_in_create = BIAImpactCriterionCreate(
            name=criterion_name,
            description="To be deleted",
            bia_category_id=test_bia_category.id,
            levels=[BIAImpactCriterionLevelCreate(level_name="Temp", score=1)]
        )
        created_criterion = await service.create_criterion_with_levels(
            criterion_in=criterion_in_create, organization_id=org_id, user_id=user_id
        )
        assert created_criterion is not None

        # 2. Delete the criterion
        deleted_criterion_response = await service.delete_criterion(
            criterion_id=created_criterion.id, 
            organization_id=org_id
        )

        # 3. Verify deletion response
        assert deleted_criterion_response is not None
        assert deleted_criterion_response.id == created_criterion.id
        assert deleted_criterion_response.name == criterion_name # Service returns the deleted object

        # 4. Attempt to fetch again and assert not found
        refetched_criterion = await service.get_criterion_by_id(
            criterion_id=created_criterion.id, 
            organization_id=org_id
        )
        assert refetched_criterion is None
