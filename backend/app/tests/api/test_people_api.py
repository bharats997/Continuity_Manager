# backend/app/tests/api/test_people_api.py
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from fastapi import status

from backend.app.models.domain.roles import Role as RoleModel
from backend.app.models.domain.people import Person as PersonModel, people_roles_association
from backend.app.models.person import PersonCreate, PersonUpdate, Person as PersonSchema # Pydantic models

# Helper function to create and assign a specific role to the default user
def setup_user_with_role(db: Session, role_name: str, role_description: str = "Test role") -> tuple[PersonModel, RoleModel]:
    role = db.query(RoleModel).filter(RoleModel.name == role_name).first()
    if not role:
        role = RoleModel(name=role_name, description=role_description)
        db.add(role)
        db.flush() # Flush to get role.id

    default_user = db.query(PersonModel).filter(PersonModel.id == 1).first()
    # Ensure default_user is not None, though conftest should guarantee it.
    if not default_user:
        # This should not happen if conftest.py's db_session works as expected.
        raise Exception("Default user (ID 1) not found in test setup.")

    # Check if role is already assigned
    is_role_assigned = False
    for assigned_role in default_user.roles:
        if assigned_role.id == role.id:
            is_role_assigned = True
            break
    
    if not is_role_assigned:
        # Use the association table for M2M relationship
        stmt = people_roles_association.insert().values(personId=default_user.id, roleId=role.id)
        db.execute(stmt)
        db.commit() # Commit role assignment for the test user
        db.refresh(default_user) # Refresh to see the roles in the user object
        # To ensure relationships are loaded after refresh, especially if using joinedload elsewhere or expecting .roles to be populated:
        db.refresh(default_user, attribute_names=['roles'])

    return default_user, role

# Alias for clarity in existing tests
def setup_admin_user(db: Session):
    return setup_user_with_role(db, "Admin", "Administrator role")


@pytest.mark.asyncio
async def test_create_person_as_admin(
    test_client: AsyncClient, 
    db_session: Session # db_session fixture from conftest.py
):
    # Setup: Ensure default user (ID 1) has Admin role
    admin_user, _ = setup_admin_user(db_session)
    # Ensure the admin_user object is the one used by the test client's auth dependency
    # This is implicitly handled by the deps.py using user ID 1 from db_session.

    person_data = {
        "firstName": "ApiTest",
        "lastName": "User",
        "email": "api.test.user@example.com",
        "jobTitle": "Tester",
        "departmentId": None, # Optional, can add department creation later
        "locationId": None,   # Optional, can add location creation later
        "roleIds": []         # Optional, roles for the new user
    }

    response = await test_client.post("/api/v1/people/", json=person_data)

    assert response.status_code == status.HTTP_201_CREATED
    created_person = response.json()

    assert created_person["email"] == person_data["email"]
    assert created_person["firstName"] == person_data["firstName"]
    assert created_person["lastName"] == person_data["lastName"]
    assert created_person["jobTitle"] == person_data["jobTitle"]
    assert created_person["isActive"] == True # Default
    assert "id" in created_person
    assert "organizationId" in created_person # Should be org 1
    assert created_person["organizationId"] == 1 # Default user is in org 1
    assert "createdAt" in created_person
    assert "updatedAt" in created_person
    assert created_person["createdBy"] == 1 # Default admin user ID is 1
    assert created_person["updatedBy"] == 1 # Default admin user ID is 1

    # Verify in DB
    db_person = db_session.query(PersonModel).filter(PersonModel.email == person_data["email"]).first()
    assert db_person is not None
    assert db_person.firstName == person_data["firstName"]
    assert db_person.createdBy == 1

# More tests will follow: 
# - test_create_person_duplicate_email
# - test_create_person_invalid_department_id

@pytest.mark.asyncio
async def test_create_person_invalid_department_id(
    test_client: AsyncClient, 
    db_session: Session
):
    # Setup: Ensure default user (ID 1) has Admin role
    admin_user, _ = setup_admin_user(db_session)

    non_existent_department_id = 99999
    person_data = {
        "firstName": "InvalidDept",
        "lastName": "TestUser",
        "email": "invalid.dept.test@example.com",
        "jobTitle": "Tester",
        "departmentId": non_existent_department_id,
        "roleIds": []
    }

    response = await test_client.post("/api/v1/people/", json=person_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_detail = response.json()
    assert error_detail["detail"] == f"Department with ID {non_existent_department_id} not found in this organization."

# - test_create_person_invalid_location_id

@pytest.mark.asyncio
async def test_create_person_invalid_location_id(
    test_client: AsyncClient, 
    db_session: Session
):
    # Setup: Ensure default user (ID 1) has Admin role
    admin_user, _ = setup_admin_user(db_session)
    current_organization_id = admin_user.organizationId # Should be 1

    non_existent_location_id = 88888
    person_data = {
        "firstName": "InvalidLoc",
        "lastName": "TestUser",
        "email": "invalid.loc.test@example.com",
        "jobTitle": "Tester",
        "locationId": non_existent_location_id,
        "roleIds": []
    }

    response = await test_client.post("/api/v1/people/", json=person_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_detail = response.json()
    expected_detail = f"Location with ID {non_existent_location_id} not found in organization {current_organization_id}."
    assert error_detail["detail"] == expected_detail

# - test_create_person_invalid_role_ids

@pytest.mark.asyncio
async def test_create_person_with_invalid_role_ids(
    test_client: AsyncClient, 
    db_session: Session # db_session fixture from conftest.py
):
    # Setup: Ensure default user (ID 1) has Admin role
    admin_user, _ = setup_admin_user(db_session)

    non_existent_role_ids = [77777, 88888] # Assuming these IDs don't exist
    person_data = {
        "firstName": "InvalidRole",
        "lastName": "TestUser",
        "email": "invalid.role.test@example.com",
        "jobTitle": "Tester",
        "roleIds": non_existent_role_ids
    }

    response = await test_client.post("/api/v1/people/", json=person_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_detail = response.json()
    assert error_detail["detail"] == "One or more role IDs are invalid."


@pytest.mark.asyncio
async def test_create_person_duplicate_email(
    test_client: AsyncClient, 
    db_session: Session
):
    # Setup: Ensure default user (ID 1) has Admin role
    admin_user, _ = setup_admin_user(db_session)

    unique_email = "duplicate.email.test@example.com"
    person_data_1 = {
        "firstName": "DuplicateEmail",
        "lastName": "TestUser1",
        "email": unique_email,
        "jobTitle": "Tester",
        "roleIds": [] # Required field for PersonCreate
    }

    # Create the first person
    response1 = await test_client.post("/api/v1/people/", json=person_data_1)
    assert response1.status_code == status.HTTP_201_CREATED
    created_person_id = response1.json()["id"]

    # Attempt to create a second person with the same email in the same organization
    person_data_2 = {
        "firstName": "DuplicateEmail",
        "lastName": "TestUser2",
        "email": unique_email, # Same email
        "jobTitle": "Another Tester",
        "roleIds": [] # Required field for PersonCreate
    }

    response2 = await test_client.post("/api/v1/people/", json=person_data_2)
    assert response2.status_code == status.HTTP_409_CONFLICT
    error_detail = response2.json()
    assert error_detail["detail"] == "A person with this email already exists in this organization."

    # Clean up the created person (optional, as db_session fixture rolls back)
    # person_to_delete = db_session.get(PersonModel, created_person_id)
    # if person_to_delete:
    #     db_session.delete(person_to_delete)
    #     db_session.commit()

@pytest.mark.asyncio
async def test_create_person_as_non_admin(
    test_client: AsyncClient, 
    db_session: Session # db_session fixture from conftest.py
):
    # Ensure default user (ID 1) does NOT have Admin role for this test.
    # The default user from conftest.py doesn't have roles unless explicitly added.
    # We can optionally remove 'Admin' role if it was added by another test, 
    # but pytest fixtures should provide isolation. Here, we simply don't call setup_admin_user.

    # Sanity check: Verify the default user doesn't have Admin role initially for this test session
    default_user = db_session.query(PersonModel).filter(PersonModel.id == 1).first()
    assert default_user is not None
    admin_role = db_session.query(RoleModel).filter(RoleModel.name == "Admin").first()
    if admin_role:
        assert admin_role not in default_user.roles

    person_data = {
        "firstName": "ForbiddenApiTest",
        "lastName": "User",
        "email": "forbidden.api.test.user@example.com",
        "jobTitle": "Intruder",
    }

    response = await test_client.post("/api/v1/people/", json=person_data)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    error_detail = response.json()
    assert error_detail["detail"] == "You do not have permission to manage people."

# - test_list_people

@pytest.mark.asyncio
async def test_list_people_as_bcm_manager(
    test_client: AsyncClient, 
    db_session: Session
):
    # Setup: Ensure default user (ID 1) has BCM Manager role
    bcm_manager_user, _ = setup_user_with_role(db_session, "BCM Manager", "BCM Manager role")

    # Create some people in the same organization (orgId 1)
    person1_email = "list.test.user1@example.com"
    person2_email = "list.test.user2@example.com"
    person3_email = "list.test.user3.inactive@example.com"

    # Ensure these test users don't exist from previous failed runs if any
    for email_to_clear in [person1_email, person2_email, person3_email]:
        existing = db_session.query(PersonModel).filter(PersonModel.email == email_to_clear, PersonModel.organizationId == 1).first()
        if existing:
            db_session.delete(existing)
    db_session.commit()

    db_session.add(PersonModel(firstName="List1", lastName="User", email=person1_email, organizationId=1, createdBy=bcm_manager_user.id, updatedBy=bcm_manager_user.id, isActive=True))
    db_session.add(PersonModel(firstName="List2", lastName="User", email=person2_email, organizationId=1, createdBy=bcm_manager_user.id, updatedBy=bcm_manager_user.id, isActive=True))
    db_session.add(PersonModel(firstName="List3", lastName="UserInactive", email=person3_email, organizationId=1, createdBy=bcm_manager_user.id, updatedBy=bcm_manager_user.id, isActive=False))
    db_session.commit()

    # Test without filter (should default to is_active=True)
    # This will include the default active user (ID 1) from conftest.py
    response = await test_client.get("/api/v1/people/")
    assert response.status_code == status.HTTP_200_OK
    people_list = response.json()
    assert len(people_list) == 3 # default.user + List1 + List2 (all active in org 1)
    emails_in_response = {p['email'] for p in people_list}
    assert "default.user@example.com" in emails_in_response
    assert person1_email in emails_in_response
    assert person2_email in emails_in_response
    assert person3_email not in emails_in_response

    # Test with is_active=True
    response_active = await test_client.get("/api/v1/people/?is_active=true")
    assert response_active.status_code == status.HTTP_200_OK
    people_list_active = response_active.json()
    assert len(people_list_active) == 3 # default.user + List1 + List2

    # Test with is_active=False
    response_inactive = await test_client.get("/api/v1/people/?is_active=false")
    assert response_inactive.status_code == status.HTTP_200_OK
    people_list_inactive = response_inactive.json()
    assert len(people_list_inactive) == 1
    assert people_list_inactive[0]['email'] == person3_email

    # Test with is_active=None (or not provided in a way that means 'all' - current API defaults to True if param not 'false')
    # The API endpoint has `is_active: Optional[bool] = Query(True, ...)`
    # To get all, the service layer `get_people` needs `is_active=None`
    # The endpoint currently doesn't seem to have a way to pass `None` to get all via query param easily unless `is_active` is not sent at all
    # and the service layer interprets absence of filter as 'all'.
    # Let's check service: `get_people(..., is_active: Optional[bool] = None)`
    # If `is_active` is `None` in service, it fetches all. If `True` or `False`, it filters.
    # The API `Query(True, ...)` means if `is_active` is not in query, it's `True`.
    # To test fetching ALL, we might need to adjust API or test service directly.
    # For now, assuming current behavior: if is_active query param is absent, it defaults to True.

    # Cleanup (optional, as db_session fixture rolls back)
    # db_session.query(PersonModel).filter(PersonModel.email.in_([person1_email, person2_email, person3_email])).delete(synchronize_session=False)
    # db_session.commit()


# - test_get_person_by_id

@pytest.mark.asyncio
async def test_get_person_by_id_as_admin(
    test_client: AsyncClient, 
    db_session: Session
):
    # Setup: Ensure default user (ID 1) has Admin role
    admin_user, admin_role_obj = setup_admin_user(db_session)
    expected_org_id = admin_user.organizationId # Fetch and store org ID immediately

    # Create a person to retrieve
    person_to_get_email = "get.this.person@example.com"
    person_data = {
        "firstName": "GetThis",
        "lastName": "Person",
        "email": person_to_get_email,
        "jobTitle": "Target",
        "roleIds": [admin_role_obj.id] # Assign admin role for testing roles field
    }
    response_create = await test_client.post("/api/v1/people/", json=person_data)
    assert response_create.status_code == status.HTTP_201_CREATED
    created_person_id = response_create.json()["id"]
    created_person_org_id = response_create.json()["organizationId"]
    assert created_person_org_id == expected_org_id

    # Retrieve the person
    response_get = await test_client.get(f"/api/v1/people/{created_person_id}")
    assert response_get.status_code == status.HTTP_200_OK
    retrieved_person = response_get.json()

    assert retrieved_person["id"] == created_person_id
    assert retrieved_person["email"] == person_to_get_email
    assert retrieved_person["firstName"] == "GetThis"
    assert retrieved_person["organizationId"] == expected_org_id
    assert len(retrieved_person["roles"]) == 1
    assert retrieved_person["roles"][0]["name"] == "Admin"

@pytest.mark.asyncio
async def test_get_person_not_found(
    test_client: AsyncClient, 
    db_session: Session
):
    # Setup: Ensure default user (ID 1) has Admin role (or any valid role for read access)
    setup_user_with_role(db_session, "Admin") # Admin can read

    non_existent_person_id = 999888777
    response = await test_client.get(f"/api/v1/people/{non_existent_person_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_detail = response.json()
    assert error_detail["detail"] == "Person not found"


# - test_update_person

@pytest.mark.asyncio
async def test_update_person_as_admin(
    test_client: AsyncClient, 
    db_session: Session
):
    # Setup: Ensure default user (ID 1) has Admin role
    admin_user, admin_role_obj_temp = setup_user_with_role(db_session, "Admin", "Administrator Role")
    admin_role_id = admin_role_obj_temp.id # Get ID immediately
    # Create another role for testing role updates
    _, bcm_manager_role_obj_temp = setup_user_with_role(db_session, "BCM Manager", "BCM Manager Role")
    bcm_manager_role_id = bcm_manager_role_obj_temp.id # Get ID immediately
    
    expected_org_id = admin_user.organizationId

    # Create a person to update
    person_to_update_email = "update.this.person@example.com"
    create_data = {
        "firstName": "InitialName",
        "lastName": "User",
        "email": person_to_update_email,
        "jobTitle": "InitialJob",
        "roleIds": [admin_role_id]
    }
    response_create = await test_client.post("/api/v1/people/", json=create_data)
    assert response_create.status_code == status.HTTP_201_CREATED
    created_person = response_create.json()
    created_person_id = created_person["id"]

    # Update payload
    update_data = {
        "firstName": "UpdatedName",
        "jobTitle": "UpdatedJobTitle",
        "isActive": False,
        "roleIds": [bcm_manager_role_id] # Change role
    }

    response_update = await test_client.put(f"/api/v1/people/{created_person_id}", json=update_data)
    assert response_update.status_code == status.HTTP_200_OK
    updated_person_response = response_update.json()

    assert updated_person_response["id"] == created_person_id
    assert updated_person_response["firstName"] == "UpdatedName"
    assert updated_person_response["jobTitle"] == "UpdatedJobTitle"
    assert updated_person_response["isActive"] is False
    assert updated_person_response["email"] == person_to_update_email # Email should not change unless specified
    assert len(updated_person_response["roles"]) == 1
    assert updated_person_response["roles"][0]["name"] == "BCM Manager"

    # Verify in DB
    db_session.expire_all() # Ensure fresh data from DB
    db_person = db_session.get(PersonModel, created_person_id)
    assert db_person is not None
    assert db_person.firstName == "UpdatedName"
    assert db_person.jobTitle == "UpdatedJobTitle"
    assert db_person.isActive is False
    assert len(db_person.roles) == 1
    assert db_person.roles[0].name == "BCM Manager"

@pytest.mark.asyncio
async def test_update_person_not_found(
    test_client: AsyncClient, 
    db_session: Session
):
    # Setup: Ensure default user (ID 1) has Admin role
    setup_user_with_role(db_session, "Admin")

    non_existent_person_id = 999888776
    update_data = {
        "firstName": "GhostName"
    }
    response = await test_client.put(f"/api/v1/people/{non_existent_person_id}", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_detail = response.json()
    assert error_detail["detail"] == "Person not found"


# - test_soft_delete_person

@pytest.mark.asyncio
async def test_soft_delete_person_as_admin(
    test_client: AsyncClient, 
    db_session: Session
):
    admin_user_obj, admin_role_obj = setup_admin_user(db_session)
    admin_user_id = admin_user_obj.id
    admin_role_id = admin_role_obj.id

    # Create a person to delete
    person_to_delete_email = "delete.this.person@example.com"
    create_data = {
        "firstName": "ToDelete",
        "lastName": "User",
        "email": person_to_delete_email,
        "jobTitle": "Target",
        "roleIds": [admin_role_id],
        "isActive": True
    }
    response_create = await test_client.post("/api/v1/people/", json=create_data)
    assert response_create.status_code == status.HTTP_201_CREATED
    created_person_id = response_create.json()["id"]

    # Soft delete the person
    response_delete = await test_client.delete(f"/api/v1/people/{created_person_id}")
    assert response_delete.status_code == status.HTTP_200_OK
    deleted_person_response = response_delete.json()

    assert deleted_person_response["id"] == created_person_id
    assert deleted_person_response["isActive"] is False
    assert deleted_person_response["email"] == person_to_delete_email # Email should remain

    # Verify in DB
    db_session.expire_all()
    db_person = db_session.get(PersonModel, created_person_id)
    assert db_person is not None
    assert db_person.isActive is False
    assert db_person.updatedBy == admin_user_id
    # Fields deletedAt and deletedBy are not part of the Person model

@pytest.mark.asyncio
async def test_soft_delete_person_not_found(
    test_client: AsyncClient, 
    db_session: Session
):
    setup_admin_user(db_session) # Admin context needed for the endpoint
    non_existent_person_id = 999777666
    response = await test_client.delete(f"/api/v1/people/{non_existent_person_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Person not found"

@pytest.mark.asyncio
async def test_soft_delete_already_inactive_person(
    test_client: AsyncClient, 
    db_session: Session
):
    admin_user_obj, admin_role_obj = setup_admin_user(db_session)
    admin_role_id = admin_role_obj.id

    # Create and immediately soft delete a person
    person_email = "already.inactive@example.com"
    create_data = {"firstName": "InactiveTest", "lastName": "User", "email": person_email, "jobTitle": "Tester", "roleIds": [admin_role_id]}
    response_create = await test_client.post("/api/v1/people/", json=create_data)
    person_id = response_create.json()["id"]
    
    await test_client.delete(f"/api/v1/people/{person_id}") # First delete

    # Attempt to delete again
    response_second_delete = await test_client.delete(f"/api/v1/people/{person_id}")
    assert response_second_delete.status_code == status.HTTP_400_BAD_REQUEST
    assert response_second_delete.json()["detail"] == "Person is already inactive."


@pytest.mark.asyncio
async def test_update_person_duplicate_email(
    test_client: AsyncClient, 
    db_session: Session
):
    admin_user, admin_role_id_obj = setup_admin_user(db_session)
    admin_role_id = admin_role_id_obj.id
    expected_org_id = admin_user.organizationId

    # Create person 1 (the one whose email will be duplicated)
    person1_email = "unique.person1@example.com"
    p1_data = {"firstName": "P1", "lastName": "User", "email": person1_email, "jobTitle": "T1", "roleIds": [admin_role_id]}
    await test_client.post("/api/v1/people/", json=p1_data) # Don't need the response

    # Create person 2 (the one to be updated)
    person2_initial_email = "person.to.update@example.com"
    p2_data = {"firstName": "P2", "lastName": "User", "email": person2_initial_email, "jobTitle": "T2", "roleIds": [admin_role_id]}
    resp_p2_create = await test_client.post("/api/v1/people/", json=p2_data)
    p2_id = resp_p2_create.json()["id"]

    # Attempt to update person 2's email to person 1's email
    update_payload = {"email": person1_email}
    response = await test_client.put(f"/api/v1/people/{p2_id}", json=update_payload)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "A person with this email already exists in this organization."

@pytest.mark.asyncio
async def test_update_person_invalid_department_id(
    test_client: AsyncClient, 
    db_session: Session
):
    admin_user, admin_role_id_obj = setup_admin_user(db_session)
    admin_role_id = admin_role_id_obj.id

    # Create a person to update
    person_data = {"firstName": "DeptTest", "lastName": "User", "email": "dept.update.test@example.com", "jobTitle": "Tester", "roleIds": [admin_role_id]}
    response_create = await test_client.post("/api/v1/people/", json=person_data)
    person_id = response_create.json()["id"]

    invalid_dept_id = 998877
    update_payload = {"departmentId": invalid_dept_id}
    response = await test_client.put(f"/api/v1/people/{person_id}", json=update_payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"Department with ID {invalid_dept_id} not found in this organization."

@pytest.mark.asyncio
async def test_update_person_invalid_location_id(
    test_client: AsyncClient, 
    db_session: Session
):
    admin_user, admin_role_id_obj = setup_admin_user(db_session)
    admin_role_id = admin_role_id_obj.id
    expected_org_id = admin_user.organizationId # For the error message

    # Create a person to update
    person_data = {"firstName": "LocTest", "lastName": "User", "email": "loc.update.test@example.com", "jobTitle": "Tester", "roleIds": [admin_role_id]}
    response_create = await test_client.post("/api/v1/people/", json=person_data)
    person_id = response_create.json()["id"]

    invalid_loc_id = 776655
    update_payload = {"locationId": invalid_loc_id}
    response = await test_client.put(f"/api/v1/people/{person_id}", json=update_payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"Location with ID {invalid_loc_id} not found in organization {expected_org_id}."

@pytest.mark.asyncio
async def test_update_person_invalid_role_ids(
    test_client: AsyncClient, 
    db_session: Session
):
    admin_user, admin_role_id_obj = setup_admin_user(db_session)
    admin_role_id = admin_role_id_obj.id

    # Create a person to update
    person_data = {"firstName": "RoleUpdateTest", "lastName": "User", "email": "role.update.test@example.com", "jobTitle": "Tester", "roleIds": [admin_role_id]}
    response_create = await test_client.post("/api/v1/people/", json=person_data)
    person_id = response_create.json()["id"]

    invalid_role_ids = [999888, 777666]
    update_payload = {"roleIds": invalid_role_ids}
    response = await test_client.put(f"/api/v1/people/{person_id}", json=update_payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "One or more role IDs are invalid for update."

