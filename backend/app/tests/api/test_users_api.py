# backend/app/tests/api/test_people_api.py
import uuid

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.domain.users import User as UserModel, user_roles_association # Updated people_roles_association to user_roles_association
from app.models.domain.roles import Role as RoleModel
from app.schemas.users import UserCreate, UserUpdate
from app.tests.helpers import DEFAULT_USER_ID, DEFAULT_ORG_ID

# Helper function to create and assign a specific role to the default user
def setup_user_with_role(db: Session, role_name: str, role_description: str = "Test role") -> tuple[UserModel, RoleModel]:
    role = db.query(RoleModel).filter(RoleModel.name == role_name).first()
    if not role:
        role = RoleModel(name=role_name, description=role_description)
        db.add(role)
        db.flush() # Flush to get role.id

    default_user = db.query(UserModel).filter(UserModel.id == DEFAULT_USER_ID).first()
    # Ensure default_user is not None, though conftest should guarantee it.
    if not default_user:
        # This should not happen if conftest.py's db_session works as expected.
        raise Exception(f"Default user (ID {DEFAULT_USER_ID}) not found in test setup.")

    # Check if role is already assigned
    is_role_assigned = False
    for assigned_role in default_user.roles:
        if assigned_role.id == role.id:
            is_role_assigned = True
            break
    
    if not is_role_assigned:
        # Use the association table for M2M relationship
        stmt = user_roles_association.insert().values(userId=default_user.id, roleId=role.id) # Changed personId to userId
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
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    # Setup: Ensure default user (ID 1) has Admin role
    admin_user, _ = setup_admin_user(db_session)
    expected_admin_user_id_str = str(admin_user.id)
    expected_admin_org_id_str = str(admin_user.organizationId)
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

    response = await authenticated_test_client.post("/api/v1/people/", json=person_data)

    assert response.status_code == status.HTTP_201_CREATED
    created_person_json = response.json()

    assert created_person_json["email"] == person_data["email"]
    assert created_person_json["firstName"] == person_data["firstName"]
    assert "id" in created_person_json
    assert "createdAt" in created_person_json
    assert "updatedAt" in created_person_json
    
    # Key assertions for organization and audit fields
    assert created_person_json["organizationId"] == expected_admin_org_id_str
    assert created_person_json["createdBy"] == expected_admin_user_id_str
    assert created_person_json["updatedBy"] == expected_admin_user_id_str # On create, updatedBy is same as createdBy

    # Verify in DB
    created_person_id = uuid.UUID(created_person_json["id"])
    # The API call should have committed the session, so we query directly.
    retrieved_person_from_db = db_session.get(PersonModel, created_person_id)
    assert retrieved_person_from_db is not None
    # Use pre-captured string IDs for comparison:
    assert str(retrieved_person_from_db.organizationId) == expected_admin_org_id_str
    assert str(retrieved_person_from_db.createdBy) == expected_admin_user_id_str
    assert str(retrieved_person_from_db.updatedBy) == expected_admin_user_id_str
    db_person = db_session.query(PersonModel).filter(PersonModel.email == person_data["email"]).first()
    assert db_person is not None
    assert db_person.firstName == person_data["firstName"]
    assert str(db_person.createdBy) == expected_admin_user_id_str

# More tests will follow: 
# - test_create_person_duplicate_email
# - test_create_person_invalid_department_id

@pytest.mark.asyncio
async def test_create_person_invalid_department_id(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    # Setup: Ensure default user (ID 1) has Admin role
    admin_user, admin_role_id_obj = setup_admin_user(db_session)
    admin_role_id = admin_role_id_obj.id

    invalid_dept_id = str(uuid.uuid4()) # Use a valid, non-existent UUID string
    person_data = {
        "firstName": "InvalidDeptTest", 
        "lastName": "User", 
        "email": "invalid.dept.test@example.com", 
        "jobTitle": "Tester", 
        "departmentId": invalid_dept_id,
        "roleIds": [str(admin_role_id)]
    }

    response = await authenticated_test_client.post("/api/v1/people/", json=person_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_detail = response.json()
    assert error_detail["detail"] == f"Department with ID {invalid_dept_id} not found in this organization."


@pytest.mark.asyncio
async def test_create_person_invalid_location_id(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    # Setup: Ensure default user (ID 1) has Admin role
    admin_user, admin_role_id_obj = setup_admin_user(db_session)
    admin_role_id = admin_role_id_obj.id

    # Optionally create a department and location to ensure they exist if needed
    # For this test, we are testing invalid location ID, so actual location doesn't matter

    invalid_loc_id = str(uuid.uuid4())
    person_data = {
        "firstName": "InvalidLocTest", 
        "lastName": "User", 
        "email": "invalid.loc.test@example.com", 
        "jobTitle": "Tester", 
        "locationId": invalid_loc_id, 
        "roleIds": [str(admin_role_id)]
    }

    response = await authenticated_test_client.post("/api/v1/people/", json=person_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_detail = response.json()
    assert error_detail["detail"] == f"Location with ID {invalid_loc_id} not found in organization {str(admin_user.organizationId)}."


# - test_create_person_invalid_role_ids

@pytest.mark.asyncio
async def test_create_person_with_invalid_role_ids(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    # Setup: Ensure default user (ID 1) has Admin role
    admin_user, _ = setup_admin_user(db_session)

    non_existent_role_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    person_data = {
        "firstName": "InvalidRole",
        "lastName": "TestUser",
        "email": "invalid.role.test@example.com",
        "jobTitle": "Tester",
        "roleIds": non_existent_role_ids
    }

    response = await authenticated_test_client.post("/api/v1/people/", json=person_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_detail = response.json()
    assert error_detail["detail"] == "One or more role IDs are invalid."


@pytest.mark.asyncio
async def test_create_person_duplicate_email(
    authenticated_test_client: AsyncClient, 
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
        "roleIds": []
    }

    # Create the first person
    response1 = await authenticated_test_client.post("/api/v1/people/", json=person_data_1)
    assert response1.status_code == status.HTTP_201_CREATED
    created_person_id = response1.json()["id"]

    person_data_2 = {
        "firstName": "DuplicateEmail",
        "lastName": "TestUser2",
        "email": unique_email,
        "jobTitle": "Another Tester",
        "roleIds": []
    }

    response2 = await authenticated_test_client.post("/api/v1/people/", json=person_data_2)
    assert response2.status_code == status.HTTP_409_CONFLICT
    error_detail = response2.json()
    assert error_detail["detail"] == "A person with this email already exists in this organization."


# - test_create_person_as_non_admin

@pytest.mark.asyncio
async def test_create_person_as_non_admin(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    # Ensure default user (ID 1) does NOT have Admin role for this test.

    default_user = db_session.query(PersonModel).filter(PersonModel.id == DEFAULT_USER_ID).first()
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

    response = await authenticated_test_client.post("/api/v1/people/", json=person_data)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    error_detail = response.json()
    assert error_detail["detail"] == "You do not have permission to manage people."


# - test_list_people

@pytest.mark.asyncio
async def test_list_people_as_bcm_manager(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    bcm_manager_user, _ = setup_user_with_role(db_session, "BCM Manager", "BCM Manager role")

    person1_email = "list.test.user1@example.com"
    person2_email = "list.test.user2@example.com"
    person3_email = "list.test.user3.inactive@example.com"

    for email_to_clear in [person1_email, person2_email, person3_email]:
        existing = db_session.query(PersonModel).filter(PersonModel.email == email_to_clear, PersonModel.organizationId == DEFAULT_ORG_ID).first()
        if existing:
            db_session.delete(existing)
    db_session.commit()

    db_session.add(PersonModel(firstName="List1", lastName="User", email=person1_email, organizationId=DEFAULT_ORG_ID, createdBy=bcm_manager_user.id, updatedBy=bcm_manager_user.id, isActive=True))
    db_session.add(PersonModel(firstName="List2", lastName="User", email=person2_email, organizationId=DEFAULT_ORG_ID, createdBy=bcm_manager_user.id, updatedBy=bcm_manager_user.id, isActive=True))
    db_session.add(PersonModel(firstName="List3", lastName="UserInactive", email=person3_email, organizationId=DEFAULT_ORG_ID, createdBy=bcm_manager_user.id, updatedBy=bcm_manager_user.id, isActive=False))
    db_session.commit()

    response = await authenticated_test_client.get("/api/v1/people/")
    assert response.status_code == status.HTTP_200_OK
    people_list = response.json()
    assert len(people_list) == 3
    emails_in_response = {p['email'] for p in people_list}
    assert "default.user@example.com" in emails_in_response
    assert person1_email in emails_in_response
    assert person2_email in emails_in_response
    assert person3_email not in emails_in_response

    response_active = await authenticated_test_client.get("/api/v1/people/?is_active=true")
    assert response_active.status_code == status.HTTP_200_OK
    people_list_active = response_active.json()
    assert len(people_list_active) == 3

    response_inactive = await authenticated_test_client.get("/api/v1/people/?is_active=false")
    assert response_inactive.status_code == status.HTTP_200_OK
    people_list_inactive = response_inactive.json()
    assert len(people_list_inactive) == 1
    assert people_list_inactive[0]['email'] == person3_email

    assert len(people_list_inactive) == 1
    assert people_list_inactive[0]['email'] == person3_email

@pytest.mark.asyncio
async def test_get_person_by_id_as_admin(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    admin_user, admin_role_obj = setup_admin_user(db_session)
    expected_org_id = admin_user.organizationId

    person_to_get_email = "get.this.person@example.com"
    person_data = {
        "firstName": "GetThis",
        "lastName": "Person",
        "email": person_to_get_email,
        "jobTitle": "Target",
        "roleIds": [str(admin_role_obj.id)]
    }
    response_create = await authenticated_test_client.post("/api/v1/people/", json=person_data)
    assert response_create.status_code == status.HTTP_201_CREATED
    created_person_id = response_create.json()["id"]
    created_person_org_id = response_create.json()["organizationId"]
    assert created_person_org_id == str(expected_org_id)

    response_get = await authenticated_test_client.get(f"/api/v1/people/{created_person_id}")
    assert response_get.status_code == status.HTTP_200_OK
    retrieved_person = response_get.json()

    assert retrieved_person["id"] == created_person_id
    assert retrieved_person["email"] == person_to_get_email
    assert retrieved_person["firstName"] == "GetThis"
    assert retrieved_person["organizationId"] == str(expected_org_id)
    assert len(retrieved_person["roles"]) == 1
    assert retrieved_person["roles"][0]["name"] == "Admin"

@pytest.mark.asyncio
async def test_get_person_not_found(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    setup_user_with_role(db_session, "Admin")

    non_existent_person_id = str(uuid.uuid4())
    response = await authenticated_test_client.get(f"/api/v1/people/{non_existent_person_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Person not found"

# - test_update_person

@pytest.mark.asyncio
async def test_update_person_as_admin(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    admin_user, admin_role_obj_temp = setup_admin_user(db_session)
    admin_role_id = admin_role_obj_temp.id
    _, bcm_manager_role_obj_temp = setup_user_with_role(db_session, "BCM Manager", "BCM Manager Role")
    bcm_manager_role_id = bcm_manager_role_obj_temp.id
    
    expected_org_id = admin_user.organizationId

    person_to_update_email = "update.this.person@example.com"
    create_data = {
        "firstName": "InitialName",
        "lastName": "User",
        "email": person_to_update_email,
        "jobTitle": "InitialJob",
        "roleIds": [str(admin_role_id)]
    }
    response_create = await authenticated_test_client.post("/api/v1/people/", json=create_data)
    assert response_create.status_code == status.HTTP_201_CREATED
    created_person = response_create.json()
    created_person_id = created_person["id"]

    update_data = {
        "firstName": "UpdatedName",
        "jobTitle": "UpdatedJobTitle",
        "isActive": False,
        "roleIds": [str(bcm_manager_role_id)]
    }

    response_update = await authenticated_test_client.put(f"/api/v1/people/{created_person_id}", json=update_data)
    assert response_update.status_code == status.HTTP_200_OK
    updated_person_response = response_update.json()

    assert updated_person_response["id"] == created_person_id
    assert updated_person_response["firstName"] == "UpdatedName"
    assert updated_person_response["jobTitle"] == "UpdatedJobTitle"
    assert updated_person_response["isActive"] is False
    assert updated_person_response["email"] == person_to_update_email
    assert len(updated_person_response["roles"]) == 1
    assert updated_person_response["roles"][0]["name"] == "BCM Manager"

    db_session.expire_all()
    db_person = db_session.get(PersonModel, uuid.UUID(created_person_id))
    assert db_person is not None
    assert db_person.firstName == "UpdatedName"
    assert db_person.jobTitle == "UpdatedJobTitle"
    assert db_person.isActive is False
    assert len(db_person.roles) == 1
    assert db_person.roles[0].name == "BCM Manager"

@pytest.mark.asyncio
async def test_update_person_not_found(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    setup_user_with_role(db_session, "Admin")

    non_existent_person_id = str(uuid.uuid4())
    update_data = {"jobTitle": "Ghost Hunter"}
    response = await authenticated_test_client.put(f"/api/v1/people/{non_existent_person_id}", json=update_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_detail = response.json()
    assert error_detail["detail"] == "Person not found"

# - test_soft_delete_person

@pytest.mark.asyncio
async def test_soft_delete_person_as_admin(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    admin_user_obj, admin_role_obj = setup_admin_user(db_session)
    admin_user_id = admin_user_obj.id
    admin_role_id = admin_role_obj.id

    person_to_delete_email = "delete.this.person@example.com"
    create_data = {
        "firstName": "ToDelete",
        "lastName": "User",
        "email": person_to_delete_email,
        "jobTitle": "Target",
        "roleIds": [str(admin_role_id)],
        "isActive": True
    }
    response_create = await authenticated_test_client.post("/api/v1/people/", json=create_data)
    assert response_create.status_code == status.HTTP_201_CREATED
    created_person_id = response_create.json()["id"]

    response_delete = await authenticated_test_client.delete(f"/api/v1/people/{created_person_id}")
    assert response_delete.status_code == status.HTTP_200_OK
    deleted_person_response = response_delete.json()

    assert deleted_person_response["id"] == created_person_id
    assert deleted_person_response["isActive"] is False
    assert deleted_person_response["email"] == person_to_delete_email

    # Verify in DB
    db_session.expire_all()
    db_person = db_session.get(PersonModel, uuid.UUID(created_person_id)) # Cast to UUID
    assert db_person is not None
    assert db_person.isActive is False
    assert db_person.updatedBy == admin_user_id

@pytest.mark.asyncio
async def test_soft_delete_person_not_found(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    setup_admin_user(db_session)
    non_existent_person_id = str(uuid.uuid4())
    response = await authenticated_test_client.delete(f"/api/v1/people/{non_existent_person_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Person not found"

@pytest.mark.asyncio
async def test_soft_delete_already_inactive_person(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    admin_user_obj, admin_role_obj = setup_admin_user(db_session)
    admin_role_id = admin_role_obj.id

    person_email = "already.inactive@example.com"
    create_data = {"firstName": "InactiveTest", "lastName": "User", "email": person_email, "jobTitle": "Tester", "roleIds": [str(admin_role_id)]}
    response_create = await authenticated_test_client.post("/api/v1/people/", json=create_data)
    person_id = response_create.json()["id"]
    
    await authenticated_test_client.delete(f"/api/v1/people/{person_id}")

    response_second_delete = await authenticated_test_client.delete(f"/api/v1/people/{person_id}")
    assert response_second_delete.status_code == status.HTTP_400_BAD_REQUEST
    assert response_second_delete.json()["detail"] == "Person is already inactive."


@pytest.mark.asyncio
async def test_update_person_duplicate_email(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    admin_user, admin_role_id_obj = setup_admin_user(db_session)
    admin_role_id = admin_role_id_obj.id
    expected_org_id = admin_user.organizationId

    person1_email = "unique.person1@example.com"
    p1_data = {"firstName": "P1", "lastName": "User", "email": person1_email, "jobTitle": "T1", "roleIds": [str(admin_role_id)]}
    await authenticated_test_client.post("/api/v1/people/", json=p1_data)

    person2_initial_email = "person.to.update@example.com"
    p2_data = {"firstName": "P2", "lastName": "User", "email": person2_initial_email, "jobTitle": "T2", "roleIds": [str(admin_role_id)]}
    resp_p2_create = await authenticated_test_client.post("/api/v1/people/", json=p2_data)
    p2_id = resp_p2_create.json()["id"]

    update_payload = {"email": person1_email}
    response = await authenticated_test_client.put(f"/api/v1/people/{p2_id}", json=update_payload)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "A person with this email already exists in this organization."

@pytest.mark.asyncio
async def test_update_person_invalid_department_id(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    admin_user, admin_role_id_obj = setup_admin_user(db_session)
    admin_role_id = admin_role_id_obj.id

    # Create a person to update
    person_data = {"firstName": "DeptTest", "lastName": "User", "email": "dept.update.test@example.com", "jobTitle": "Tester", "roleIds": [str(admin_role_id)]}
    response_create = await authenticated_test_client.post("/api/v1/people/", json=person_data)
    person_id = response_create.json()["id"]

    invalid_dept_id = str(uuid.uuid4())
    update_payload = {"departmentId": invalid_dept_id}
    response = await authenticated_test_client.put(f"/api/v1/people/{str(person_id)}", json=update_payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"Department with ID {invalid_dept_id} not found in this organization."

@pytest.mark.asyncio
async def test_update_person_invalid_location_id(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    admin_user, admin_role_id_obj = setup_admin_user(db_session)
    admin_role_id = admin_role_id_obj.id
    expected_org_id = admin_user.organizationId

    person_data = {"firstName": "LocTest", "lastName": "User", "email": "loc.update.test@example.com", "jobTitle": "Tester", "roleIds": [str(admin_role_id)]}
    response_create = await authenticated_test_client.post("/api/v1/people/", json=person_data)
    person_id = response_create.json()["id"]

    invalid_loc_id = str(uuid.uuid4())
    update_payload = {"locationId": invalid_loc_id}
    response = await authenticated_test_client.put(f"/api/v1/people/{str(person_id)}", json=update_payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"Location with ID {invalid_loc_id} not found in organization {str(expected_org_id)}."

@pytest.mark.asyncio
async def test_update_person_invalid_role_ids(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    admin_user, admin_role_id_obj = setup_admin_user(db_session)
    admin_role_id = admin_role_id_obj.id

    # Create a person to update
    person_data = {"firstName": "RoleUpdateTest", "lastName": "User", "email": "role.update.test@example.com", "jobTitle": "Tester", "roleIds": [str(admin_role_id)]}
    response_create = await authenticated_test_client.post("/api/v1/people/", json=person_data)
    person_id = response_create.json()["id"]

    invalid_role_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    update_payload = {"roleIds": invalid_role_ids}
    response = await authenticated_test_client.put(f"/api/v1/people/{str(person_id)}", json=update_payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "One or more role IDs are invalid for update."

