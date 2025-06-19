import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain.users import User
from app.schemas.role import RoleName # Corrected import
from app.models.domain.bia_impact_criteria import BIAImpactCriterion, RatingTypeEnum
from app.schemas.bia_frameworks import BIAFrameworkCreate, BIAFrameworkParameterCreate, BIAFrameworkRTOCreate

pytestmark = pytest.mark.asyncio

# Helper to create BIA Impact Criteria for framework parameters
async def create_test_impact_criteria(db_session: AsyncSession, organization_id: uuid.UUID, user_id: uuid.UUID, count: int = 2) -> list[BIAImpactCriterion]:
    criteria = []
    for i in range(count):
        criterion = BIAImpactCriterion(
            name=f'Test Criterion {i}',
            description=f'Test Description {i}',
            rating_type=RatingTypeEnum.QUALITATIVE,
            organization_id=organization_id,
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db_session.add(criterion)
        criteria.append(criterion)
    await db_session.commit()
    for c in criteria:
        await db_session.refresh(c)
    return criteria

class TestBIAFrameworksAPI:
    async def test_create_bia_framework_success(self, async_client: AsyncClient, async_db_session: AsyncSession, async_client_authenticated_as_user_factory):
        """Test successful creation of a BIA Framework with valid data by an authorized user."""
        # 1. Arrange: Create an authorized user (BCM_MANAGER)
        _ignored_client, bcm_manager_token, bcm_manager_user = await async_client_authenticated_as_user_factory(
            user_identifier="bcm_manager_for_success_test@example.com", 
            role_override=RoleName.BCM_MANAGER,
            permissions_to_assign_to_role=["bia_frameworks:create"] # Added permission
        )
        headers = {"Authorization": f"Bearer {bcm_manager_token}"}

        # Create prerequisite impact criteria
        criteria = await create_test_impact_criteria(async_db_session, bcm_manager_user.organization_id, bcm_manager_user.id, 2)
        criterion1_id = criteria[0].id
        criterion2_id = criteria[1].id

        # Define the framework payload
        framework_data = BIAFrameworkCreate(
            name="Standard Financial Impact Framework",
            description="A framework to assess financial impact based on revenue loss and operational costs.",
            formula="WEIGHTED_AVERAGE",
            threshold=3.5,
            parameters=[
                BIAFrameworkParameterCreate(criterion_id=criterion1_id, weightage=60.0),
                BIAFrameworkParameterCreate(criterion_id=criterion2_id, weightage=40.0),
            ],
            rtos=[
                BIAFrameworkRTOCreate(display_text="Critical (0-4 Hours)", value_in_hours=4),
                BIAFrameworkRTOCreate(display_text="Urgent (4-24 Hours)", value_in_hours=24),
            ]
        )

        # 2. Act: Make the API call
        response = await async_client.post("/api/v1/bia-frameworks/", headers=headers, json=framework_data.model_dump(mode='json'))

        # 3. Assert: Check the response
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == framework_data.name
        assert data["threshold"] == framework_data.threshold
        assert data["organization_id"] == str(bcm_manager_user.organization_id)
        assert len(data["parameters"]) == 2
        assert len(data["rtos"]) == 2
        assert data["parameters"][0]["weightage"] == 60.0
        assert data["rtos"][0]["value_in_hours"] == 4

    async def test_create_bia_framework_unauthorized_role(self, async_client: AsyncClient, async_client_authenticated_as_user_factory):
        """Test that a user with an unauthorized role cannot create a BIA Framework."""
        # 1. Arrange: Create an unauthorized user (USER)
        _ignored_client, user_token, user_user = await async_client_authenticated_as_user_factory(
            user_identifier="user_for_unauthorized_test@example.com", 
            role_override=RoleName.USER
            # No specific permissions needed as this user should be unauthorized
        )
        headers = {"Authorization": f"Bearer {user_token}"}

        # Dummy data, content doesn't matter as it should fail on auth
        framework_data = {
            "name": "Unauthorized Framework",
            "description": "This should not be created.",
            "formula": "WEIGHTED_AVERAGE",
            "threshold": 1.0,
            "parameters": [],
            "rtos": []
        }

        # 2. Act: Make the API call
        response = await async_client.post("/api/v1/bia-frameworks/", headers=headers, json=framework_data)

        # 3. Assert: Check for 403 Forbidden
        assert response.status_code == 403
        assert response.json()["detail"] == "User does not have the required permissions."

    async def test_create_bia_framework_invalid_weightage(self, async_client: AsyncClient, async_db_session: AsyncSession, async_client_authenticated_as_user_factory):
        """Test creation of a BIA Framework fails if parameter weightages do not sum to 100."""
        # 1. Arrange: Create an authorized user
        _ignored_client, bcm_manager_token, bcm_manager_user = await async_client_authenticated_as_user_factory(
            user_identifier="bcm_manager_for_invalid_weightage_test@example.com", 
            role_override=RoleName.BCM_MANAGER,
            permissions_to_assign_to_role=["bia_frameworks:create"] # Added permission
        )
        headers = {"Authorization": f"Bearer {bcm_manager_token}"}

        # Create prerequisite impact criteria
        criteria = await create_test_impact_criteria(async_db_session, bcm_manager_user.organization_id, bcm_manager_user.id, 2)
        criterion1_id = criteria[0].id
        criterion2_id = criteria[1].id

        # Define the framework payload with invalid weightages (sum != 100)
        framework_data = BIAFrameworkCreate(
            name="Invalid Weightage Framework",
            description="This framework has incorrect weightages.",
            formula="WEIGHTED_AVERAGE",
            threshold=3.5,
            parameters=[
                BIAFrameworkParameterCreate(criterion_id=criterion1_id, weightage=50.0), # Sum is 90, not 100
                BIAFrameworkParameterCreate(criterion_id=criterion2_id, weightage=40.0),
            ],
            rtos=[]
        )

        # 2. Act: Make the API call
        response = await async_client.post("/api/v1/bia-frameworks/", headers=headers, json=framework_data.model_dump(mode='json'))

        # 3. Assert: Check for 400 Bad Request
        assert response.status_code == 400
        assert "The sum of all parameter weightages must be 100" in response.json()["detail"]
