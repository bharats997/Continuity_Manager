import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update as sqlalchemy_update
from datetime import datetime
from typing import Callable, Dict, Any, List, Optional, AsyncGenerator, Awaitable

from app.models.domain.users import User as UserModel
# from app.models.domain.roles import Role as RoleModel # Not directly used in this file now
from app.models.domain.vendors import Vendor as VendorModel
from app.schemas.role import RoleName
from app.schemas.vendors import VendorCreate, VendorUpdate, VendorRead
from app.models.vendor import VendorCriticality
from app.tests.helpers import (
    create_role_with_permissions_async,
    create_user_with_roles_async,
    DEFAULT_ORG_ID
)
from app.tests.conftest import async_client_authenticated_as_user_factory # Main factory for authenticated clients

# API Prefix
VENDORS_API_PREFIX = "/api/v1/vendors"

# Helper to create a vendor payload
def create_vendor_payload(
    name: str = "Test Vendor Inc.", 
    criticality: VendorCriticality = VendorCriticality.MEDIUM,
    contact_person: Optional[str] = "John Doe",
    contact_email: Optional[str] = "john.doe@testvendor.com",
    service_provided: Optional[str] = "Critical IT Services"
) -> Dict[str, Any]:
    return {
        "name": name,
        "criticality": criticality.value,
        "contact_person": contact_person,
        "contact_email": contact_email,
        "service_provided": service_provided
    }

@pytest_asyncio.fixture(scope="function")
async def default_organization_id() -> uuid.UUID:
    return DEFAULT_ORG_ID # Using the one from conftest

@pytest_asyncio.fixture(scope="function")
async def admin_user(
    async_db_session: AsyncSession, 
    default_organization_id: uuid.UUID
) -> UserModel:
    # Ensure ADMIN role exists for the organization
    await create_role_with_permissions_async(
        db_session=async_db_session, 
        role_name=RoleName.ADMIN.value, 
        permissions_names=[], # Add relevant permissions if needed for vendor mgmt
        organization_id=default_organization_id
    )
    user = await create_user_with_roles_async(
        db_session=async_db_session,
        email="admin.vendor@test.com",
        first_name="Admin",
        last_name="User",
        role_names=[RoleName.ADMIN.value],
        organization_id=default_organization_id
    )
    return user

@pytest_asyncio.fixture(scope="function")
async def standard_user(
    async_db_session: AsyncSession, 
    default_organization_id: uuid.UUID
) -> UserModel:
    # Ensure USER role exists for the organization
    await create_role_with_permissions_async(
        db_session=async_db_session, 
        role_name=RoleName.USER.value, 
        permissions_names=[], 
        organization_id=default_organization_id
    )
    user = await create_user_with_roles_async(
        db_session=async_db_session,
        email="user.vendor@test.com",
        first_name="Standard",
        last_name="User",
        role_names=[RoleName.USER.value],
        organization_id=default_organization_id
    )
    return user

@pytest_asyncio.fixture(scope="function")
async def admin_client(
    async_client_authenticated_as_user_factory: Callable[[UserModel], Awaitable[AsyncClient]],
    admin_user: UserModel
) -> AsyncClient:
    return await async_client_authenticated_as_user_factory(admin_user)
        
@pytest_asyncio.fixture(scope="function")
async def standard_user_client(
    async_client_authenticated_as_user_factory: Callable[[UserModel], Awaitable[AsyncClient]],
    standard_user: UserModel
) -> AsyncClient:
    return await async_client_authenticated_as_user_factory(standard_user)

@pytest.mark.asyncio
async def test_create_vendor_as_admin_success(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession, # Renamed db_session to async_db_session for consistency
    admin_user: UserModel # Added admin_user fixture
):
    """Test successful vendor creation by an admin user."""
    payload = create_vendor_payload(name="Admin Created Vendor")
    response = await admin_client.post(VENDORS_API_PREFIX + "/", json=payload)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["criticality"] == payload["criticality"]
    assert data["contact_person"] == payload["contact_person"]
    assert data["contact_email"] == payload["contact_email"]
    assert data["service_provided"] == payload["service_provided"]
    assert "id" in data
    assert data["is_active"] is True # Explicitly check boolean value
    # Check if 'id' is a valid UUID
    assert uuid.UUID(data["id"])
    assert data["created_by_id"] == str(admin_user.id)
    assert data["updated_by_id"] == str(admin_user.id)
    assert data["organization_id"] == str(admin_user.organization_id)

    # Verify in DB
    vendor_in_db = await async_db_session.get(VendorModel, uuid.UUID(data["id"]))
    assert vendor_in_db is not None
    assert vendor_in_db.name == payload["name"]
    assert vendor_in_db.criticality.value == payload["criticality"] # Compare enum's value
    assert vendor_in_db.contact_person == payload["contact_person"]
    assert vendor_in_db.contact_email == payload["contact_email"]
    assert vendor_in_db.service_provided == payload["service_provided"]
    assert vendor_in_db.is_active is True
    assert vendor_in_db.created_by_id == admin_user.id
    assert vendor_in_db.updated_by_id == admin_user.id
    assert vendor_in_db.organization_id == admin_user.organization_id

@pytest.mark.asyncio
async def test_create_vendor_as_non_admin_forbidden(
    standard_user_client: AsyncClient, 
    async_db_session: AsyncSession
):
    """Test vendor creation attempt by a non-admin user is forbidden."""
    payload = create_vendor_payload(name="Non-Admin Vendor Attempt")
    response = await standard_user_client.post(VENDORS_API_PREFIX + "/", json=payload)
    assert response.status_code == 403, response.text

@pytest.mark.asyncio
async def test_create_vendor_duplicate_name_conflict(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession 
):
    """Test creating a vendor with a duplicate name results in HTTP 409 Conflict."""
    payload = create_vendor_payload(name="Duplicate Test Vendor")
    # Create the first vendor
    response1 = await admin_client.post(VENDORS_API_PREFIX + "/", json=payload)
    assert response1.status_code == 201, response1.text

    # Attempt to create a second vendor with the same name
    response2 = await admin_client.post(VENDORS_API_PREFIX + "/", json=payload)
    assert response2.status_code == 409, response2.text # Expect 409 Conflict 

@pytest.mark.asyncio
async def test_create_vendor_missing_name_bad_request(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession
):
    """Test creating a vendor with missing required field (name) results in 422 Unprocessable Entity."""
    payload = create_vendor_payload(name="Valid Name But Will Be Removed")
    del payload["name"] # Remove required field
    
    response = await admin_client.post(VENDORS_API_PREFIX + "/", json=payload)
    assert response.status_code == 422, response.text # FastAPI/Pydantic validation

@pytest.mark.asyncio
async def test_create_vendor_invalid_email_bad_request(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession
):
    """Test creating a vendor with an invalid email format results in HTTP 422."""
    payload = create_vendor_payload(
        name="Vendor Invalid Email Test", 
        contact_email="not-an-email"
    )
    response = await admin_client.post(VENDORS_API_PREFIX + "/", json=payload)
    assert response.status_code == 422, response.text

@pytest.mark.asyncio
async def test_create_vendor_invalid_criticality_bad_request(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession
):
    """Test creating a vendor with an invalid criticality value results in HTTP 422."""
    payload = create_vendor_payload(
        name="Vendor Invalid Criticality Test", 
        criticality="VERY_HIGH" # Not a valid enum value
    )
    response = await admin_client.post(VENDORS_API_PREFIX + "/", json=payload)
    assert response.status_code == 422, response.text

# More tests to be added for other CRUD operations, RBAC, validation, etc.


@pytest_asyncio.fixture(scope="function")
async def bcm_manager_user(
    async_db_session: AsyncSession, 
    default_organization_id: uuid.UUID
) -> UserModel:
    await create_role_with_permissions_async(
        db_session=async_db_session, 
        role_name=RoleName.BCM_MANAGER.value, 
        permissions_names=["read:vendor"], 
        organization_id=default_organization_id
    )
    user = await create_user_with_roles_async(
        db_session=async_db_session,
        email="bcm.manager.vendor@test.com",
        first_name="BCM",
        last_name="Manager",
        role_names=[RoleName.BCM_MANAGER.value],
        organization_id=default_organization_id
    )
    return user

@pytest_asyncio.fixture(scope="function")
async def bcm_manager_client(
    async_client_authenticated_as_user_factory: Callable[[UserModel], Awaitable[AsyncClient]],
    bcm_manager_user: UserModel
) -> AsyncClient:
    return await async_client_authenticated_as_user_factory(bcm_manager_user)

# --- Read Vendor (Single) Tests ---
@pytest.mark.asyncio
async def test_read_vendor_as_admin_success(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession,
    admin_user: UserModel # To get current_user_id and organization_id
):
    """Test admin can successfully read an existing vendor."""
    payload = create_vendor_payload(name="Readable Vendor by Admin")
    create_response = await admin_client.post(VENDORS_API_PREFIX + "/", json=payload)
    assert create_response.status_code == 201, create_response.text
    vendor_id = create_response.json()["id"]

    read_response = await admin_client.get(f"{VENDORS_API_PREFIX}/{vendor_id}")
    assert read_response.status_code == 200, read_response.text
    data = read_response.json()
    assert data["id"] == vendor_id
    assert data["name"] == payload["name"]
    assert data["organization_id"] == str(admin_user.organization_id)

@pytest.mark.asyncio
async def test_read_vendor_as_bcm_manager_success(
    bcm_manager_client: AsyncClient, 
    admin_client: AsyncClient, # To create the vendor initially
    async_db_session: AsyncSession,
    bcm_manager_user: UserModel
):
    """Test BCM Manager can successfully read an existing vendor."""
    payload = create_vendor_payload(name="Readable Vendor by BCM Manager")
    # Create vendor as admin first
    create_response = await admin_client.post(VENDORS_API_PREFIX + "/", json=payload)
    assert create_response.status_code == 201, create_response.text
    vendor_id = create_response.json()["id"]

    read_response = await bcm_manager_client.get(f"{VENDORS_API_PREFIX}/{vendor_id}")
    assert read_response.status_code == 200, read_response.text
    data = read_response.json()
    assert data["id"] == vendor_id
    assert data["name"] == payload["name"]
    assert data["organization_id"] == str(bcm_manager_user.organization_id)

@pytest.mark.asyncio
async def test_read_vendor_as_ciso_success(
    ciso_client: AsyncClient, 
    admin_client: AsyncClient, # To create the vendor initially
    async_db_session: AsyncSession,
    ciso_user: UserModel
):
    """Test CISO can successfully read an existing vendor."""
    payload = create_vendor_payload(name="Readable Vendor by CISO")
    # Create vendor as admin first
    create_response = await admin_client.post(VENDORS_API_PREFIX + "/", json=payload)
    assert create_response.status_code == 201, create_response.text
    vendor_id = create_response.json()["id"]

    read_response = await ciso_client.get(f"{VENDORS_API_PREFIX}/{vendor_id}")
    assert read_response.status_code == 200, read_response.text
    data = read_response.json()
    assert data["id"] == vendor_id
    assert data["name"] == payload["name"]
    assert data["organization_id"] == str(ciso_user.organization_id)

@pytest.mark.asyncio
async def test_read_vendor_as_standard_user_forbidden(
    standard_user_client: AsyncClient, 
    admin_client: AsyncClient, # To create the vendor initially
    async_db_session: AsyncSession
):
    """Test standard user is forbidden to read a vendor."""
    payload = create_vendor_payload(name="Unreadable Vendor by Standard User")
    create_response = await admin_client.post(VENDORS_API_PREFIX + "/", json=payload)
    assert create_response.status_code == 201, create_response.text
    vendor_id = create_response.json()["id"]

    read_response = await standard_user_client.get(f"{VENDORS_API_PREFIX}/{vendor_id}")
    assert read_response.status_code == 403, read_response.text

@pytest.mark.asyncio
async def test_read_vendor_not_found(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession
):
    """Test reading a non-existent vendor returns 404 Not Found."""
    non_existent_vendor_id = uuid.uuid4()
    response = await admin_client.get(f"{VENDORS_API_PREFIX}/{non_existent_vendor_id}")
    assert response.status_code == 404, response.text

@pytest.mark.asyncio
async def test_read_vendor_different_organization_forbidden(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession,
    default_organization_id: uuid.UUID, # Fixture for current user's org ID
    async_client_authenticated_as_user_factory: Callable[..., AsyncGenerator[AsyncClient, None]]
):
    """Test reading a vendor from a different organization is forbidden (results in 404)."""
    # 1. Create a user and role in a *different* organization
    other_org_id = uuid.uuid4()
    await create_role_with_permissions_async(db_session=async_db_session, role_name=RoleName.ADMIN.value, permissions_names=[], organization_id=other_org_id)
    other_admin_user = await create_user_with_roles_async(
        db_session=async_db_session, 
        email="other.admin.vendor@test.com", # Ensure unique email for this user
        first_name="Other",
        last_name="Admin",
        role_names=[RoleName.ADMIN.value], 
        organization_id=other_org_id
    )
    
    # 2. Get an authenticated client for this 'other_admin_user'
    other_admin_client = await async_client_authenticated_as_user_factory(other_admin_user)
    
    # 3. Create a vendor in that 'other' organization using 'other_admin_client'
    other_vendor_payload = create_vendor_payload(name="Vendor in Other Org")
    create_other_response = await other_admin_client.post(VENDORS_API_PREFIX + "/", json=other_vendor_payload)
    assert create_other_response.status_code == 201, create_other_response.text
    other_vendor_id = create_other_response.json()["id"]

    # 4. Attempt to read this 'other_vendor_id' using the original 'admin_client' (from default_organization_id)
    response = await admin_client.get(f"{VENDORS_API_PREFIX}/{other_vendor_id}")
    # Service's get_vendor_by_id checks organization_id and raises NotFoundException if not matched
    assert response.status_code == 404, response.text


@pytest_asyncio.fixture(scope="function")
async def ciso_user(
    async_db_session: AsyncSession, 
    default_organization_id: uuid.UUID
) -> UserModel:
    await create_role_with_permissions_async(
        db_session=async_db_session, 
        role_name=RoleName.CISO.value, 
        permissions_names=["read:vendor"], 
        organization_id=default_organization_id
    )
    user = await create_user_with_roles_async(
        db_session=async_db_session,
        email="ciso.vendor@test.com",
        first_name="CISO",
        last_name="User",
        role_names=[RoleName.CISO.value],
        organization_id=default_organization_id
    )
    return user

@pytest_asyncio.fixture(scope="function")
async def ciso_client(
    async_client_authenticated_as_user_factory: Callable[[UserModel], Awaitable[AsyncClient]],
    ciso_user: UserModel
) -> AsyncClient:
    return await async_client_authenticated_as_user_factory(ciso_user)

# --- List Vendors Tests ---
@pytest.mark.asyncio
async def test_list_vendors_as_admin_success(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession,
    admin_user: UserModel
):
    """Test admin can successfully list vendors."""
    # Create a couple of vendors
    payload1 = create_vendor_payload(name="List Vendor 1 by Admin")
    payload2 = create_vendor_payload(name="List Vendor 2 by Admin")
    await admin_client.post(VENDORS_API_PREFIX + "/", json=payload1)
    await admin_client.post(VENDORS_API_PREFIX + "/", json=payload2)

    response = await admin_client.get(VENDORS_API_PREFIX + "/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data
    assert len(data["items"]) >= 2 # Could be more if other tests created vendors in same org
    assert data["total"] >= 2
    # Check if the created vendors are in the list (order might vary)
    vendor_names_in_response = [v["name"] for v in data["items"]]
    assert payload1["name"] in vendor_names_in_response
    assert payload2["name"] in vendor_names_in_response
    for item in data["items"]:
        assert item["organization_id"] == str(admin_user.organization_id)

@pytest.mark.asyncio
async def test_list_vendors_as_bcm_manager_success(
    bcm_manager_client: AsyncClient, 
    admin_client: AsyncClient, # To create vendors
    async_db_session: AsyncSession,
    bcm_manager_user: UserModel
):
    """Test BCM Manager can successfully list vendors."""
    payload1 = create_vendor_payload(name="List Vendor 1 by BCM")
    payload2 = create_vendor_payload(name="List Vendor 2 by BCM")
    await admin_client.post(VENDORS_API_PREFIX + "/", json=payload1) # Create with admin
    await admin_client.post(VENDORS_API_PREFIX + "/", json=payload2)

    response = await bcm_manager_client.get(VENDORS_API_PREFIX + "/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["items"]) >= 2
    vendor_names_in_response = [v["name"] for v in data["items"]]
    assert payload1["name"] in vendor_names_in_response
    assert payload2["name"] in vendor_names_in_response
    for item in data["items"]:
        assert item["organization_id"] == str(bcm_manager_user.organization_id)

@pytest.mark.asyncio
async def test_list_vendors_as_ciso_success(
    ciso_client: AsyncClient, 
    admin_client: AsyncClient, # To create vendors
    async_db_session: AsyncSession,
    ciso_user: UserModel
):
    """Test CISO can successfully list vendors."""
    payload1 = create_vendor_payload(name="List Vendor 1 by CISO")
    payload2 = create_vendor_payload(name="List Vendor 2 by CISO")
    await admin_client.post(VENDORS_API_PREFIX + "/", json=payload1) # Create with admin
    await admin_client.post(VENDORS_API_PREFIX + "/", json=payload2)

    response = await ciso_client.get(VENDORS_API_PREFIX + "/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["items"]) >= 2
    vendor_names_in_response = [v["name"] for v in data["items"]]
    assert payload1["name"] in vendor_names_in_response
    assert payload2["name"] in vendor_names_in_response
    for item in data["items"]:
        assert item["organization_id"] == str(ciso_user.organization_id)

@pytest.mark.asyncio
async def test_list_vendors_as_standard_user_forbidden(
    standard_user_client: AsyncClient, 
    admin_client: AsyncClient, # To create a vendor so the list isn't empty
    async_db_session: AsyncSession
):
    """Test standard user is forbidden to list vendors."""
    payload = create_vendor_payload(name="Vendor for Standard User List Test")
    await admin_client.post(VENDORS_API_PREFIX + "/", json=payload)

    response = await standard_user_client.get(VENDORS_API_PREFIX + "/")
    assert response.status_code == 403, response.text

@pytest.mark.asyncio
async def test_list_vendors_pagination(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession
):
    """Test pagination for listing vendors."""
    # Create 3 vendors
    names = [f"Paginate Vendor {i}" for i in range(3)]
    for name in names:
        await admin_client.post(VENDORS_API_PREFIX + "/", json=create_vendor_payload(name=name))
    
    # Get first page, size 2
    response_page1 = await admin_client.get(f"{VENDORS_API_PREFIX}/?page=1&size=2")
    assert response_page1.status_code == 200, response_page1.text
    data_page1 = response_page1.json()
    assert len(data_page1["items"]) == 2
    assert data_page1["page"] == 1
    assert data_page1["size"] == 2
    # Total should be at least 3, could be more from other tests
    # To make this test more robust, we might need to count vendors for this org before creating new ones
    # or ensure a clean slate, but for now, >=3 is a reasonable check if tests run sequentially on same DB.
    assert data_page1["total"] >= 3 

    # Get second page, size 2
    response_page2 = await admin_client.get(f"{VENDORS_API_PREFIX}/?page=2&size=2")
    assert response_page2.status_code == 200, response_page2.text
    data_page2 = response_page2.json()
    # This will have 1 item if total is 3, or more if total is >3
    assert len(data_page2["items"]) >= 1 
    assert data_page2["page"] == 2
    assert data_page2["size"] == 2

    # Ensure items are different across pages (assuming default sort order is consistent)
    ids_page1 = {item["id"] for item in data_page1["items"]}
    ids_page2 = {item["id"] for item in data_page2["items"]}
    assert not (ids_page1 & ids_page2) # No overlap

@pytest.mark.asyncio
async def test_list_vendors_empty_for_organization(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession,
    default_organization_id: uuid.UUID,
    async_client_authenticated_as_user_factory: Callable[..., AsyncGenerator[AsyncClient, None]]
):
    """Test listing vendors returns an empty list for an organization with no vendors."""
    # Create a new organization and an admin user in it
    new_org_id = uuid.uuid4()
    await create_role_with_permissions_async(db_session=async_db_session, role_name=RoleName.ADMIN.value, permissions_names=[], organization_id=new_org_id)
    new_org_admin_user = await create_user_with_roles_async(
        db_session=async_db_session, 
        email="new.org.admin.vendor@test.com", 
        first_name="New",
        last_name="Admin",
        role_names=[RoleName.ADMIN.value], 
        organization_id=new_org_id
    )
    new_org_admin_client = await async_client_authenticated_as_user_factory(new_org_admin_user)

    response = await new_org_admin_client.get(VENDORS_API_PREFIX + "/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["items"]) == 0
    assert data["total"] == 0

@pytest.mark.asyncio
async def test_list_vendors_organization_scoping(
    admin_client: AsyncClient, # Belongs to default_organization_id
    async_db_session: AsyncSession,
    default_organization_id: uuid.UUID,
    async_client_authenticated_as_user_factory: Callable[..., AsyncGenerator[AsyncClient, None]]
):
    """Test that listing vendors only returns vendors from the user's organization."""
    # 1. Create a vendor in the default organization (using admin_client)
    default_org_vendor_name = "Vendor in Default Org for Scoping Test"
    await admin_client.post(VENDORS_API_PREFIX + "/", json=create_vendor_payload(name=default_org_vendor_name))

    # 2. Create another organization, an admin user, and a vendor in that new organization
    other_org_id = uuid.uuid4()
    await create_role_with_permissions_async(db_session=async_db_session, role_name=RoleName.ADMIN.value, permissions_names=[], organization_id=other_org_id)
    other_admin_user = await create_user_with_roles_async(
        db_session=async_db_session, 
        email="other.admin.scoping.vendor@test.com", 
        first_name="Other",
        last_name="Admin",
        role_names=[RoleName.ADMIN.value], 
        organization_id=other_org_id
    )
    other_admin_client = await async_client_authenticated_as_user_factory(other_admin_user)
    other_org_vendor_name = "Vendor in Other Org for Scoping Test"
    await other_admin_client.post(VENDORS_API_PREFIX + "/", json=create_vendor_payload(name=other_org_vendor_name))

    # 3. List vendors using the original admin_client (should only see default_org_vendor_name)
    response_default_org = await admin_client.get(VENDORS_API_PREFIX + "/")
    assert response_default_org.status_code == 200, response_default_org.text
    data_default_org = response_default_org.json()
    default_org_vendor_names = [v["name"] for v in data_default_org["items"]]
    assert default_org_vendor_name in default_org_vendor_names
    assert other_org_vendor_name not in default_org_vendor_names
    for item in data_default_org["items"]:
        assert item["organization_id"] == str(default_organization_id)

    # 4. List vendors using other_admin_client (should only see other_org_vendor_name)
    response_other_org = await other_admin_client.get(VENDORS_API_PREFIX + "/")
    assert response_other_org.status_code == 200, response_other_org.text
    data_other_org = response_other_org.json()
    other_org_vendor_names = [v["name"] for v in data_other_org["items"]]
    assert other_org_vendor_name in other_org_vendor_names
    assert default_org_vendor_name not in other_org_vendor_names
    for item in data_other_org["items"]:
        assert item["organization_id"] == str(other_org_id)


# --- Update Vendor Tests ---
@pytest.mark.asyncio
async def test_update_vendor_as_admin_success(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession,
    admin_user: UserModel
):
    """Test admin can successfully update an existing vendor."""
    # Create a vendor first
    create_payload = create_vendor_payload(name="Vendor to Update")
    create_response = await admin_client.post(VENDORS_API_PREFIX + "/", json=create_payload)
    assert create_response.status_code == 201, create_response.text
    vendor_id = create_response.json()["id"]

    update_payload = {
        "name": "Updated Vendor Name",
        "contact_email": "updated.email@example.com",
        "service_provided": "Updated service description."
    }
    response = await admin_client.put(f"{VENDORS_API_PREFIX}/{vendor_id}", json=update_payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == vendor_id
    assert data["name"] == update_payload["name"]
    assert data["contact_email"] == update_payload["contact_email"]
    assert data["service_provided"] == update_payload["service_provided"]
    assert data["organization_id"] == str(admin_user.organization_id)
    assert data["updated_by_id"] == str(admin_user.id)

@pytest.mark.asyncio
async def test_update_vendor_partial_update_success(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession,
    admin_user: UserModel
):
    """Test admin can successfully update only some fields of a vendor."""
    original_name = "Vendor for Partial Update"
    original_email = "partial.original@example.com"
    create_payload = create_vendor_payload(name=original_name, contact_email=original_email)
    create_response = await admin_client.post(VENDORS_API_PREFIX + "/", json=create_payload)
    assert create_response.status_code == 201, create_response.text
    vendor_id = create_response.json()["id"]

    update_payload = {"name": "Partially Updated Vendor Name"}
    response = await admin_client.put(f"{VENDORS_API_PREFIX}/{vendor_id}", json=update_payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == vendor_id
    assert data["name"] == update_payload["name"]
    assert data["contact_email"] == original_email # Should remain unchanged
    assert data["updated_by_id"] == str(admin_user.id)

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_client_fixture_name",
    ["bcm_manager_client", "ciso_client", "standard_user_client"]
)
async def test_update_vendor_as_non_admin_forbidden(
    request: pytest.FixtureRequest,
    user_client_fixture_name: str,
    admin_client: AsyncClient, # To create the vendor
    async_db_session: AsyncSession
):
    """Test non-admin users (BCM Manager, CISO, Standard User) are forbidden to update a vendor."""
    user_client = request.getfixturevalue(user_client_fixture_name)
    
    create_payload = create_vendor_payload(name="Vendor for Non-Admin Update Test")
    create_response = await admin_client.post(VENDORS_API_PREFIX + "/", json=create_payload)
    assert create_response.status_code == 201, create_response.text
    vendor_id = create_response.json()["id"]

    update_payload = {"name": "Attempted Update by Non-Admin"}
    response = await user_client.put(f"{VENDORS_API_PREFIX}/{vendor_id}", json=update_payload)
    assert response.status_code == 403, response.text

@pytest.mark.asyncio
async def test_update_vendor_name_conflict(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession
):
    """Test updating a vendor's name to one that already exists results in HTTP 409."""
    # Create two vendors
    vendor1_name = "Existing Vendor 1 for Conflict Test"
    vendor2_name = "Vendor to be Updated for Conflict Test"
    await admin_client.post(VENDORS_API_PREFIX + "/", json=create_vendor_payload(name=vendor1_name))
    create_response_v2 = await admin_client.post(VENDORS_API_PREFIX + "/", json=create_vendor_payload(name=vendor2_name))
    vendor2_id = create_response_v2.json()["id"]

    # Attempt to update vendor2's name to vendor1's name
    update_payload = {"name": vendor1_name}
    response = await admin_client.put(f"{VENDORS_API_PREFIX}/{vendor2_id}", json=update_payload)
    assert response.status_code == 409, response.text

@pytest.mark.asyncio
async def test_update_vendor_not_found(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession
):
    """Test updating a non-existent vendor returns 404 Not Found."""
    non_existent_vendor_id = uuid.uuid4()
    update_payload = {"name": "Update Non Existent"}
    response = await admin_client.put(f"{VENDORS_API_PREFIX}/{non_existent_vendor_id}", json=update_payload)
    assert response.status_code == 404, response.text

@pytest.mark.asyncio
async def test_update_vendor_different_organization_forbidden(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession,
    async_client_authenticated_as_user_factory: Callable[..., AsyncGenerator[AsyncClient, None]]
):
    """Test updating a vendor from a different organization is forbidden (results in 404)."""
    # Create a vendor in another organization
    other_org_id = uuid.uuid4()
    await create_role_with_permissions_async(db_session=async_db_session, role_name=RoleName.ADMIN.value, permissions_names=[], organization_id=other_org_id)
    other_admin_user = await create_user_with_roles_async(
        db_session=async_db_session, 
        email="other.admin.update.vendor@test.com", 
        first_name="Other",
        last_name="Admin",
        role_names=[RoleName.ADMIN.value], 
        organization_id=other_org_id
    )
    other_admin_client = await async_client_authenticated_as_user_factory(other_admin_user)
    create_other_response = await other_admin_client.post(VENDORS_API_PREFIX + "/", json=create_vendor_payload(name="Vendor in Other Org for Update Test"))
    other_vendor_id = create_other_response.json()["id"]

    # Attempt to update this vendor using the original admin_client
    update_payload = {"name": "Attempted Update Across Orgs"}
    response = await admin_client.put(f"{VENDORS_API_PREFIX}/{other_vendor_id}", json=update_payload)
    assert response.status_code == 404, response.text # Service's get_vendor_by_id will raise NotFound

@pytest.mark.asyncio
async def test_update_vendor_empty_name_bad_request(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession
):
    """Test updating a vendor's name to an empty string results in HTTP 422."""
    create_payload = create_vendor_payload(name="Vendor for Empty Name Update Test")
    create_response = await admin_client.post(VENDORS_API_PREFIX + "/", json=create_payload)
    vendor_id = create_response.json()["id"]

    update_payload = {"name": ""} # Empty name
    response = await admin_client.put(f"{VENDORS_API_PREFIX}/{vendor_id}", json=update_payload)
    assert response.status_code == 422, response.text # Pydantic validation error

@pytest.mark.asyncio
async def test_update_inactive_vendor_unprocessable(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession,
    admin_user: UserModel
):
    """Test attempting to update an inactive vendor results in HTTP 422."""
    # 1. Create a vendor
    create_payload = create_vendor_payload(name="Vendor to Deactivate and Update")
    create_response = await admin_client.post(VENDORS_API_PREFIX + "/", json=create_payload)
    vendor_id = create_response.json()["id"]

    # 2. Deactivate the vendor (soft delete - assuming a DELETE endpoint exists and sets is_active=False)
    # For now, let's manually update its 'is_active' status in the DB as delete endpoint is not yet tested/used.
    # This is a temporary workaround for this specific test.
    # In a full suite, we'd call the DELETE endpoint.
    stmt = (
        sqlalchemy_update(VendorModel)
        .where(VendorModel.id == uuid.UUID(vendor_id))
        .values(is_active=False, updated_by_id=admin_user.id, updated_at=datetime.utcnow())
    )
    await async_db_session.execute(stmt)
    await async_db_session.commit()

    # 3. Attempt to update the now inactive vendor
    update_payload = {"name": "Attempted Update on Inactive Vendor"}
    response = await admin_client.put(f"{VENDORS_API_PREFIX}/{vendor_id}", json=update_payload)
    assert response.status_code == 422, response.text
    error_detail = response.json()["detail"]
    assert f"Vendor with ID {vendor_id} is inactive and cannot be updated." in error_detail

@pytest.mark.asyncio
async def test_update_vendor_invalid_email_validation_error(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession
):
    """Test updating a vendor with an invalid email format results in HTTP 422."""
    # Create a vendor first
    create_payload = create_vendor_payload(name="Vendor for Invalid Email Update")
    create_response = await admin_client.post(VENDORS_API_PREFIX + "/", json=create_payload)
    assert create_response.status_code == 201, create_response.text
    vendor_id = create_response.json()["id"]

    update_payload = {"contact_email": "not-a-valid-email"}
    response = await admin_client.put(f"{VENDORS_API_PREFIX}/{vendor_id}", json=update_payload)
    assert response.status_code == 422, response.text

@pytest.mark.asyncio
async def test_update_vendor_invalid_criticality_validation_error(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession
):
    """Test updating a vendor with an invalid criticality value results in HTTP 422."""
    # Create a vendor first
    create_payload = create_vendor_payload(name="Vendor for Invalid Criticality Update")
    create_response = await admin_client.post(VENDORS_API_PREFIX + "/", json=create_payload)
    assert create_response.status_code == 201, create_response.text
    vendor_id = create_response.json()["id"]

    update_payload = {"criticality": "SUPER_DUPER_HIGH"}
    response = await admin_client.put(f"{VENDORS_API_PREFIX}/{vendor_id}", json=update_payload)
    assert response.status_code == 422, response.text


# --- Soft Delete Vendor Tests ---
@pytest.mark.asyncio
async def test_delete_vendor_as_admin_success(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession,
    admin_user: UserModel
):
    """Test admin can successfully soft delete an active vendor."""
    create_payload = create_vendor_payload(name="Vendor to Delete")
    create_response = await admin_client.post(VENDORS_API_PREFIX + "/", json=create_payload)
    assert create_response.status_code == 201, create_response.text
    vendor_id = create_response.json()["id"]

    delete_response = await admin_client.delete(f"{VENDORS_API_PREFIX}/{vendor_id}")
    assert delete_response.status_code == 200, delete_response.text
    data = delete_response.json()
    assert data["id"] == vendor_id
    assert data["is_active"] is False
    assert data["updated_by_id"] == str(admin_user.id)

    # Verify it's actually marked inactive in DB / not retrievable as active
    get_response = await admin_client.get(f"{VENDORS_API_PREFIX}/{vendor_id}")
    # The get_vendor_by_id service method does not filter by is_active itself, 
    # but the API might. If it returns the vendor regardless of active status:
    # assert get_response.status_code == 200
    # assert get_response.json()["is_active"] is False
    # However, typically, a GET for a single resource implies active. 
    # Let's assume the service's get_vendor_by_id returns it, but we should also check listing.
    # For now, let's assume the GET /id endpoint returns it even if inactive, showing its current state.
    # If the requirement is that GET /id should 404 for inactive, this test part needs adjustment.
    # Based on VendorService.get_vendor_by_id, it does NOT filter by is_active.
    assert get_response.status_code == 200, get_response.text
    assert get_response.json()["is_active"] is False

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_client_fixture_name",
    ["bcm_manager_client", "ciso_client", "standard_user_client"]
)
async def test_delete_vendor_as_non_admin_forbidden(
    request: pytest.FixtureRequest,
    user_client_fixture_name: str,
    admin_client: AsyncClient, # To create the vendor
    async_db_session: AsyncSession
):
    """Test non-admin users are forbidden to delete a vendor."""
    user_client = request.getfixturevalue(user_client_fixture_name)
    
    create_payload = create_vendor_payload(name="Vendor for Non-Admin Delete Test")
    create_response = await admin_client.post(VENDORS_API_PREFIX + "/", json=create_payload)
    assert create_response.status_code == 201, create_response.text
    vendor_id = create_response.json()["id"]

    response = await user_client.delete(f"{VENDORS_API_PREFIX}/{vendor_id}")
    assert response.status_code == 403, response.text

@pytest.mark.asyncio
async def test_delete_vendor_not_found(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession
):
    """Test deleting a non-existent vendor returns 404 Not Found."""
    non_existent_vendor_id = uuid.uuid4()
    response = await admin_client.delete(f"{VENDORS_API_PREFIX}/{non_existent_vendor_id}")
    assert response.status_code == 404, response.text

@pytest.mark.asyncio
async def test_delete_vendor_different_organization_forbidden(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession,
    async_client_authenticated_as_user_factory: Callable[..., AsyncGenerator[AsyncClient, None]]
):
    """Test deleting a vendor from a different organization is forbidden (results in 404)."""
    # Create a vendor in another organization
    other_org_id = uuid.uuid4()
    await create_role_with_permissions_async(db_session=async_db_session, role_name=RoleName.ADMIN.value, permissions_names=[], organization_id=other_org_id)
    other_admin_user = await create_user_with_roles_async(
        db_session=async_db_session, 
        email="other.admin.delete.vendor@test.com", 
        first_name="Other",
        last_name="Admin",
        role_names=[RoleName.ADMIN.value], 
        organization_id=other_org_id
    )
    other_admin_client = await async_client_authenticated_as_user_factory(other_admin_user)
    create_other_response = await other_admin_client.post(VENDORS_API_PREFIX + "/", json=create_vendor_payload(name="Vendor in Other Org for Delete Test"))
    other_vendor_id = create_other_response.json()["id"]

    # Attempt to delete this vendor using the original admin_client
    response = await admin_client.delete(f"{VENDORS_API_PREFIX}/{other_vendor_id}")
    assert response.status_code == 404, response.text # Service's get_vendor_by_id will raise NotFound

@pytest.mark.asyncio
async def test_delete_already_inactive_vendor_idempotent(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession,
    admin_user: UserModel
):
    """Test deleting an already inactive vendor is idempotent (returns 200 OK)."""
    # 1. Create and delete a vendor
    create_payload = create_vendor_payload(name="Vendor to Delete Twice")
    create_response = await admin_client.post(VENDORS_API_PREFIX + "/", json=create_payload)
    vendor_id = create_response.json()["id"]
    first_delete_response = await admin_client.delete(f"{VENDORS_API_PREFIX}/{vendor_id}")
    assert first_delete_response.status_code == 200
    assert first_delete_response.json()["is_active"] is False

    # 2. Attempt to delete it again
    second_delete_response = await admin_client.delete(f"{VENDORS_API_PREFIX}/{vendor_id}")
    assert second_delete_response.status_code == 200, second_delete_response.text
    data = second_delete_response.json()
    assert data["id"] == vendor_id
    assert data["is_active"] is False # Should still be inactive
    # updated_by_id might change if the service updates it on every call, even if already inactive.
    # Based on VendorService.delete_vendor, it returns early if not active, so updated_by_id won't change on the second call.
    assert data["updated_by_id"] == str(admin_user.id) # Should be from the first delete

@pytest.mark.asyncio
async def test_deleted_vendor_not_in_list_and_cannot_be_updated(
    admin_client: AsyncClient, 
    async_db_session: AsyncSession
):
    """Test a soft-deleted vendor is not in the active list and cannot be updated."""
    # 1. Create and delete a vendor
    vendor_name = "Deleted Vendor for List/Update Test"
    create_payload = create_vendor_payload(name=vendor_name)
    create_response = await admin_client.post(VENDORS_API_PREFIX + "/", json=create_payload)
    vendor_id = create_response.json()["id"]
    await admin_client.delete(f"{VENDORS_API_PREFIX}/{vendor_id}")

    # 2. Verify it's not in the list of active vendors
    # The list endpoint GET / should only return active vendors by default if service implements this.
    # VendorService.get_all_vendors does not currently filter by is_active. This needs to be added to the service or API.
    # For now, this part of the test might fail or pass vacuously if the list endpoint doesn't filter.
    # Assuming the list endpoint WILL be modified to only show active items:
    list_response = await admin_client.get(VENDORS_API_PREFIX + "/")
    assert list_response.status_code == 200
    listed_vendor_ids = [v["id"] for v in list_response.json()["items"]]
    assert vendor_id not in listed_vendor_ids

    # 3. Verify it cannot be updated (already covered by test_update_inactive_vendor_unprocessable)
    # This is a conceptual check here. The actual test is test_update_inactive_vendor_unprocessable.
    update_payload = {"name": "Attempt to Update Deleted Vendor"}
    update_response = await admin_client.put(f"{VENDORS_API_PREFIX}/{vendor_id}", json=update_payload)
    assert update_response.status_code == 422, update_response.text
