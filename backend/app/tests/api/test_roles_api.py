# backend/app/tests/api/test_roles_api.py
import uuid
import json

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.orm import Session, selectinload, selectinload # Added selectinload

from app.models.domain.users import User as PersonModel, user_roles_association
from app.models.domain.roles import Role as RoleModel
from app.models.domain.permissions import Permission as PermissionModel # Added
from app.schemas.role import RoleSchema, RoleCreate, RoleUpdate # Added RoleCreate, RoleUpdate
from app.apis.deps import RolePermissions # Added
from app.tests.helpers import DEFAULT_USER_ID, DEFAULT_ORG_ID
from app.services.role_service import role_service # Added role_service for direct creation if needed

def setup_test_user_with_specific_role(db: Session, role_name: str, role_description: str = "Test role") -> tuple[PersonModel, RoleModel]:
    role = db.query(RoleModel).filter(RoleModel.name == role_name).first()
    if not role:
        role = RoleModel(name=role_name, description=role_description, organization_id=DEFAULT_ORG_ID)
        db.add(role)
        db.flush()

    default_user = db.query(PersonModel).filter(PersonModel.id == DEFAULT_USER_ID).first()
    if not default_user:
        raise Exception(f"Default user (ID {DEFAULT_USER_ID}) not found in test setup.")

    is_role_assigned = any(assigned_role.id == role.id for assigned_role in default_user.roles)
    
    if not is_role_assigned:
        stmt = people_roles_association.insert().values(personId=default_user.id, roleId=role.id)
        db.execute(stmt)
        db.commit()
        db.refresh(default_user, attribute_names=['roles'])
    return default_user, role

def ensure_permissions_exist(db: Session, permission_names: list[str]) -> dict[str, PermissionModel]:
    """Ensures specified permissions exist in the DB, creates them if not."""
    created_permissions = {}
    for name in permission_names:
        permission = db.query(PermissionModel).filter(PermissionModel.name == name).first()
        if not permission:
            permission = PermissionModel(name=name, description=f"Permission for {name}")
            db.add(permission)
            db.flush() 
        created_permissions[name] = permission
    db.commit() 
    for perm_obj in created_permissions.values(): 
        if perm_obj in db.dirty or perm_obj in db.new: 
             db.refresh(perm_obj)
    return created_permissions

def create_role_with_permissions(
    db: Session, 
    role_name: str, 
    permission_names: list[str], 
    role_description: str = "Test Role with Specific Permissions"
) -> RoleModel:
    """Creates a role and assigns specified permissions to it."""
    # Ensure permissions exist
    permissions_in_db = ensure_permissions_exist(db, permission_names)
    
    # Check if role already exists
    role = db.query(RoleModel).filter(RoleModel.name == role_name).first()
    if role:
        # Role exists, update its permissions
        role.permissions = [permissions_in_db[p_name] for p_name in permission_names if p_name in permissions_in_db]
    else:
        # Role does not exist, create new role with these permissions
        role = RoleModel(
            name=role_name, 
            description=role_description,
            organization_id=DEFAULT_ORG_ID, # Added organization_id
            permissions=[permissions_in_db[p_name] for p_name in permission_names if p_name in permissions_in_db]
        )
        db.add(role)
    
    db.commit()
    db.refresh(role, attribute_names=['permissions'])
    return role

def create_predefined_roles(db: Session) -> dict[str, RoleModel]:
    roles_to_create = {
        "Admin": "Administrator role with full access",
        "BCM Manager": "Business Continuity Manager role",
        "Department Head": "Head of a department",
        "Standard User": "Standard user role with basic access"
    }
    created_roles = {}
    for name, description in roles_to_create.items():
        role = db.query(RoleModel).filter(RoleModel.name == name).first()
        if not role:
            role = RoleModel(name=name, description=description, organization_id=DEFAULT_ORG_ID)
            db.add(role)
        created_roles[name] = role
    db.commit()
    for role_obj in created_roles.values():
        db.refresh(role_obj)
    return created_roles

def setup_test_user_with_permissions(
    db: Session, 
    user_id: uuid.UUID, 
    permission_names: list[str], 
    role_name_prefix: str = "TestRoleForPerms"
) -> tuple[PersonModel, RoleModel]:
    """Sets up a user with a role that has specific permissions."""
    # 1. Ensure permissions exist and get their models
    ensure_permissions_exist(db, permission_names)
    
    # 2. Create a unique role name for this permission set
    test_role_name = f"{role_name_prefix}_{'_'.join(sorted(permission_names)).replace(':', '_')[:30]}_{uuid.uuid4().hex[:4]}"
    
    # 3. Create the role and assign these permissions to it
    role_with_perms = create_role_with_permissions(db, test_role_name, permission_names, f"Role for {', '.join(permission_names)}")

    # 4. Fetch the user
    user = db.query(PersonModel).filter(PersonModel.id == user_id).first()
    if not user:
        # This case should ideally not happen if DEFAULT_USER_ID is always present
        # Or, adapt to create a basic user if needed for specific test scenarios
        raise Exception(f"User with ID {user_id} not found for permission setup.")

    # 5. Clear existing roles and assign this new role to the user
    user.roles.clear() # Clear any existing roles to ensure clean state for the test
    db.commit() # Commit the clearing of roles
    db.refresh(user, attribute_names=['roles'])

    user.roles.append(role_with_perms)
    db.add(user)
    db.commit()
    db.refresh(user, attribute_names=['roles'])
    
    return user, role_with_perms

@pytest.mark.asyncio
async def test_list_roles_as_bcm_manager(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    predefined_roles = create_predefined_roles(db_session)
    bcm_manager_user, _ = setup_test_user_with_specific_role(db_session, "BCM Manager")

    response = await authenticated_test_client.get("/api/v1/roles/")

    assert response.status_code == status.HTTP_200_OK
    roles_list = response.json()
    
    assert len(roles_list) == len(predefined_roles) + 1
    
    response_role_names = {role['name'] for role in roles_list}
    expected_role_names = set(predefined_roles.keys())
    expected_role_names.add("Test Admin Role")
    assert response_role_names == expected_role_names

    for role_data in roles_list:
        assert "id" in role_data
        assert "name" in role_data
        assert "description" in role_data
        assert role_data["name"] in expected_role_names
        if role_data["name"] in predefined_roles:
            assert role_data["description"] == predefined_roles[role_data["name"]].description

@pytest.mark.asyncio
async def test_get_role_by_id_as_bcm_manager(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    predefined_roles = create_predefined_roles(db_session)
    bcm_manager_user, _ = setup_test_user_with_specific_role(db_session, "BCM Manager")

    admin_role_db = predefined_roles["Admin"]
    
    response = await authenticated_test_client.get(f"/api/v1/roles/{str(admin_role_db.id)}")
    
    assert response.status_code == status.HTTP_200_OK
    role_data = response.json()
    
    assert role_data["id"] == str(admin_role_db.id)
    assert role_data["name"] == admin_role_db.name
    assert role_data["description"] == admin_role_db.description

@pytest.mark.asyncio
async def test_get_role_not_found(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    create_predefined_roles(db_session)
    setup_test_user_with_specific_role(db_session, "BCM Manager")
    
    non_existent_role_id = str(uuid.uuid4())
    response = await authenticated_test_client.get(f"/api/v1/roles/{non_existent_role_id}")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Role not found"

@pytest.mark.asyncio
async def test_create_role_as_authorized_user_no_payload_permissions(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    """Test creating a role successfully by a user with 'role:create' permission, no permissions in payload."""
    # Setup: User needs 'role:create' permission.
    # The 'authenticated_test_client' uses DEFAULT_USER_ID. We give this user the permission.
    setup_test_user_with_permissions(db_session, DEFAULT_USER_ID, [RolePermissions.CREATE])

    role_name = f"Test Role {uuid.uuid4().hex[:6]}"
    role_description = "A basic test role created by an authorized user."
    payload = {
        "name": role_name,
        "description": role_description
        # No 'permission_ids' in payload initially
    }

    response = await authenticated_test_client.post("/api/v1/roles/", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    role_data = response.json()
    assert role_data["name"] == role_name
    assert role_data["description"] == role_description
    assert "id" in role_data
    assert isinstance(role_data["permissions"], list)
    assert len(role_data["permissions"]) == 0 # No permissions assigned via payload

    # Verify in DB
    db_role = db_session.query(RoleModel).filter(RoleModel.id == role_data["id"]).first()
    assert db_role is not None
    assert db_role.name == role_name
    assert len(db_role.permissions) == 0


@pytest.mark.asyncio
async def test_create_role_as_authorized_user_with_payload_permissions(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    """Test creating a role with specific permissions in payload by an authorized user."""
    # Setup: User needs 'role:create' permission.
    setup_test_user_with_permissions(db_session, DEFAULT_USER_ID, [RolePermissions.CREATE])

    # Ensure some permissions exist that can be assigned to the new role
    perm_to_assign_names = [f"testperm_read_{uuid.uuid4().hex[:4]}", f"testperm_write_{uuid.uuid4().hex[:4]}"]
    created_permissions = ensure_permissions_exist(db_session, perm_to_assign_names)
    permission_ids_to_assign = [str(p.id) for p in created_permissions.values()]

    role_name = f"Test Role With Perms {uuid.uuid4().hex[:6]}"
    role_description = "A test role with permissions assigned via payload."
    payload = {
        "name": role_name,
        "description": role_description,
        "permission_ids": permission_ids_to_assign
    }

    response = await authenticated_test_client.post("/api/v1/roles/", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    role_data = response.json()
    assert role_data["name"] == role_name
    assert role_data["description"] == role_description
    assert "id" in role_data
    
    returned_permission_ids = sorted([p["id"] for p in role_data["permissions"]])
    assert returned_permission_ids == sorted(permission_ids_to_assign)
    assert len(role_data["permissions"]) == len(permission_ids_to_assign)

    # Verify in DB
    db_role = db_session.query(RoleModel).filter(RoleModel.id == role_data["id"]).options(selectinload(RoleModel.permissions)).first()
    assert db_role is not None
    assert db_role.name == role_name
    
    db_permission_ids = sorted([str(p.id) for p in db_role.permissions])
    assert db_permission_ids == sorted(permission_ids_to_assign)
    assert len(db_role.permissions) == len(permission_ids_to_assign)


@pytest.mark.asyncio
async def test_create_role_duplicate_name(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    """Test creating a role with a duplicate name results in 409 Conflict."""
    # Setup: User needs 'role:create' permission.
    user, _ = setup_test_user_with_permissions(db_session, DEFAULT_USER_ID, [RolePermissions.CREATE])

    role_name = f"Unique Role Name {uuid.uuid4().hex[:6]}"
    initial_payload = {"name": role_name, "description": "First role"}

    # Create the first role
    response1 = await authenticated_test_client.post("/api/v1/roles/", json=initial_payload)
    assert response1.status_code == status.HTTP_201_CREATED

    # Attempt to create another role with the same name
    duplicate_payload = {"name": role_name, "description": "Second role with duplicate name"}
    response2 = await authenticated_test_client.post("/api/v1/roles/", json=duplicate_payload)

    assert response2.status_code == status.HTTP_409_CONFLICT
    error_data = response2.json()
    assert "detail" in error_data
    # Based on role_service.py, the error message includes the specific role name.
    assert error_data["detail"] == f"Role with name '{role_name}' already exists."

    # Verify only one role with this name exists in DB
    roles_in_db = db_session.query(RoleModel).filter(RoleModel.name == role_name).all()
    assert len(roles_in_db) == 1


@pytest.mark.asyncio
async def test_create_role_with_invalid_permission_ids(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    """Test creating a role with invalid (non-existent) permission IDs results in 400 Bad Request."""
    # Setup: User needs 'role:create' permission.
    setup_test_user_with_permissions(db_session, DEFAULT_USER_ID, [RolePermissions.CREATE])

    # Ensure some valid permissions exist to mix with invalid ones, or just use invalid ones
    valid_perm_name = f"valid_perm_{uuid.uuid4().hex[:4]}"
    valid_permissions = ensure_permissions_exist(db_session, [valid_perm_name])
    valid_permission_id = str(valid_permissions[valid_perm_name].id)

    invalid_permission_id1 = str(uuid.uuid4())
    invalid_permission_id2 = str(uuid.uuid4())

    role_name = f"Test Role Invalid Perms {uuid.uuid4().hex[:6]}"
    payload = json.loads(RoleCreate(
        name=role_name,
        description="Role with mixed valid/invalid permission IDs",
        permission_ids=[valid_permission_id, invalid_permission_id1, invalid_permission_id2]
    ).model_dump_json(exclude_unset=True))

    response = await authenticated_test_client.post("/api/v1/roles/", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    error_data = response.json()
    assert "detail" in error_data
    # Example: "One or more permission IDs not found: {missing_ids_str}."
    assert str(invalid_permission_id1) in error_data["detail"]
    assert str(invalid_permission_id2) in error_data["detail"]
    assert valid_permission_id not in error_data["detail"] # Ensure valid ID is not listed as missing
    assert "not found" in error_data["detail"].lower()

    # Verify role was not created
    db_role = db_session.query(RoleModel).filter(RoleModel.name == role_name).first()
    assert db_role is None


@pytest.mark.asyncio
async def test_create_role_unauthorized_user(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    """Test creating a role by a user without 'role:create' permission results in 403 Forbidden."""
    # 1. Setup: User LACKS 'role:create' permission.
    # Give some other permission to ensure they are authenticated but not authorized for create.
    unrelated_permission_name = f"unrelated_create_perm_{uuid.uuid4().hex[:4]}"
    ensure_permissions_exist(db_session, [unrelated_permission_name])
    setup_test_user_with_permissions(db_session, DEFAULT_USER_ID, [unrelated_permission_name])

    role_name = f"Attempted Role {uuid.uuid4().hex[:6]}"
    payload_dict = {
        "name": role_name,
        "description": "This role should not be created."
    }
    # For unauthorized tests, direct dict payload is fine as UUIDs aren't involved here.

    response = await authenticated_test_client.post("/api/v1/roles/", json=payload_dict)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    error_data = response.json()
    assert "detail" in error_data
    assert error_data["detail"] == f"You do not have the required permission: '{RolePermissions.CREATE}'"

    # Verify role was not created
    db_role = db_session.query(RoleModel).filter(RoleModel.name == role_name).first()
    assert db_role is None


@pytest.mark.asyncio
async def test_update_role_replace_permissions(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    """Test replacing a role's existing permissions with a new set."""
    # 1. Setup: User has 'role:update' and 'role:read'
    setup_test_user_with_permissions(db_session, DEFAULT_USER_ID, [RolePermissions.UPDATE, RolePermissions.READ])

    # 2. Create initial permission
    initial_perm_name = f"initial_perm_for_replace_{uuid.uuid4().hex[:4]}"
    initial_permission = PermissionModel(name=initial_perm_name, description="Initial permission to be replaced")
    db_session.add(initial_permission)
    db_session.commit()
    db_session.refresh(initial_permission)
    initial_perm_id_str = str(initial_permission.id)

    # 3. Create a role with the initial permission
    role_name = f"RoleForPermissionReplacement_{uuid.uuid4().hex[:6]}"
    role_to_update = RoleModel(
        name=role_name, 
        description="Role with initial permission",
        organization_id=DEFAULT_ORG_ID,
        permissions=[initial_permission] # Associate initial permission
    )
    db_session.add(role_to_update)
    db_session.commit()
    db_session.refresh(role_to_update)
    role_id_str = str(role_to_update.id)
    
    # Verify initial state
    assert len(role_to_update.permissions) == 1
    assert role_to_update.permissions[0].id == initial_permission.id

    # 4. Create new permissions to replace with
    new_perm1_name = f"new_perm_replace_1_{uuid.uuid4().hex[:4]}"
    new_perm2_name = f"new_perm_replace_2_{uuid.uuid4().hex[:4]}"
    new_permission1 = PermissionModel(name=new_perm1_name, description="New replacement permission 1")
    new_permission2 = PermissionModel(name=new_perm2_name, description="New replacement permission 2")
    db_session.add_all([new_permission1, new_permission2])
    db_session.commit()
    db_session.refresh(new_permission1)
    db_session.refresh(new_permission2)
    
    new_perm1_id = new_permission1.id # UUID object
    new_perm2_id = new_permission2.id # UUID object
    permission_ids_for_replacement = [new_perm1_id, new_perm2_id]

    # 5. Prepare update payload
    update_payload = json.loads(RoleUpdate(
        name=role_name, # Name can remain the same
        description="Role with replaced permissions.",
        permission_ids=permission_ids_for_replacement # Pass UUID objects to Pydantic model
    ).model_dump_json(exclude_unset=True))

    # 6. Call PUT endpoint
    response = await authenticated_test_client.put(
        f"/api/v1/roles/{role_id_str}", 
        json=update_payload
    )

    # 7. Assertions for PUT response
    assert response.status_code == status.HTTP_200_OK
    updated_role_data = response.json()
    assert updated_role_data["name"] == role_name
    assert updated_role_data["description"] == "Role with replaced permissions."
    
    response_permission_ids = sorted([p['id'] for p in updated_role_data.get("permissions", [])])
    expected_new_perm_ids_str = sorted([str(new_perm1_id), str(new_perm2_id)])
    assert response_permission_ids == expected_new_perm_ids_str
    assert initial_perm_id_str not in response_permission_ids

    # 8. Verify changes in the database
    role_id_uuid = uuid.UUID(role_id_str) # Convert string ID back to UUID for DB query
    role_in_db_after_update = db_session.query(RoleModel).filter(RoleModel.id == role_id_uuid).options(selectinload(RoleModel.permissions)).one()

    current_permission_ids_in_db_str = sorted([str(p.id) for p in role_in_db_after_update.permissions])
    assert current_permission_ids_in_db_str == expected_new_perm_ids_str
    
    # Verify initial permission is no longer associated
    assert initial_permission not in role_in_db_after_update.permissions

    # Clean up
    role_in_db_after_update.permissions = [] 
    db_session.commit()
    db_session.delete(role_in_db_after_update)
    db_session.delete(initial_permission)
    db_session.delete(new_permission1)
    db_session.delete(new_permission2)
    db_session.commit()


@pytest.mark.asyncio
async def test_update_role_remove_all_permissions(
    authenticated_test_client: AsyncClient, 
    db_session: Session
):
    """Test removing all permissions from a role by providing an empty list for permission_ids."""
    # 1. Setup: User has 'role:update' and 'role:read'
    setup_test_user_with_permissions(db_session, DEFAULT_USER_ID, [RolePermissions.UPDATE, RolePermissions.READ])

    # 2. Create permissions to be initially associated
    perm_to_remove_1_name = f"perm_rem_1_{uuid.uuid4().hex[:4]}"
    perm_to_remove_2_name = f"perm_rem_2_{uuid.uuid4().hex[:4]}"
    permission1 = PermissionModel(name=perm_to_remove_1_name, description="Permission to be removed 1")
    permission2 = PermissionModel(name=perm_to_remove_2_name, description="Permission to be removed 2")
    db_session.add_all([permission1, permission2])
    db_session.commit()
    db_session.refresh(permission1)
    db_session.refresh(permission2)

    # 3. Create a role with these initial permissions
    role_name = f"Role Losing Permissions {uuid.uuid4().hex[:6]}"
    role_to_update = RoleModel(
        name=role_name, 
        organization_id=DEFAULT_ORG_ID,
        permissions=[permission1, permission2]
    )
    db_session.add(role_to_update)
    db_session.commit()
    db_session.refresh(role_to_update)
    role_id_str = str(role_to_update.id)
    
    # Verify initial state
    assert len(role_to_update.permissions) == 2

    # 4. Prepare update payload with empty permission_ids list
    update_payload = json.loads(RoleUpdate(
        name=role_name,
        description="Role with all permissions removed.",
        permission_ids=[]  # Explicitly empty list
    ).model_dump_json(exclude_unset=True))

    # 5. Call PUT endpoint
    response = await authenticated_test_client.put(
        f"/api/v1/roles/{role_id_str}", 
        json=update_payload
    )

    # 6. Assertions for PUT response
    assert response.status_code == status.HTTP_200_OK
    updated_role_data = response.json()
    assert updated_role_data["name"] == role_name
    assert updated_role_data["description"] == "Role with all permissions removed."
    assert updated_role_data.get("permissions", []) == [] # Expect empty list or not present

    # 7. Verify changes in the database
    role_id_uuid = uuid.UUID(role_id_str)
    role_in_db_after_update = db_session.query(RoleModel).filter(RoleModel.id == role_id_uuid).options(selectinload(RoleModel.permissions)).one()

    assert not role_in_db_after_update.permissions # Should be an empty list

    # Clean up
    db_session.delete(role_in_db_after_update)
    db_session.delete(permission1) # These are from test_update_role_remove_all_permissions
    db_session.delete(permission2) # These are from test_update_role_remove_all_permissions
    db_session.commit()


@pytest.mark.asyncio
async def test_update_role_permissions_unchanged_if_not_provided(
    authenticated_test_client: AsyncClient,
    db_session: Session
):
    """Test that a role's permissions remain unchanged if 'permission_ids' is not in the update payload."""
    # 1. Setup: User has 'role:update' and 'role:read'
    setup_test_user_with_permissions(db_session, DEFAULT_USER_ID, [RolePermissions.UPDATE, RolePermissions.READ])

    # 2. Create initial permissions
    perm1_name = f"perm_unchanged_1_{uuid.uuid4().hex[:4]}"
    perm2_name = f"perm_unchanged_2_{uuid.uuid4().hex[:4]}"
    permission1_for_unchanged_test = PermissionModel(name=perm1_name, description="Unchanged Permission 1")
    permission2_for_unchanged_test = PermissionModel(name=perm2_name, description="Unchanged Permission 2")
    db_session.add_all([permission1_for_unchanged_test, permission2_for_unchanged_test])
    db_session.commit()
    db_session.refresh(permission1_for_unchanged_test)
    db_session.refresh(permission2_for_unchanged_test)
    initial_permission_ids = sorted([str(permission1_for_unchanged_test.id), str(permission2_for_unchanged_test.id)])
    initial_permission_names = sorted([perm1_name, perm2_name])


    # 3. Create a role with these initial permissions
    role_name = f"Role With Stable Permissions {uuid.uuid4().hex[:6]}"
    original_description = "Original description."
    role_to_update = RoleModel(
        name=role_name,
        description=original_description,
        organization_id=DEFAULT_ORG_ID,
        permissions=[permission1_for_unchanged_test, permission2_for_unchanged_test]
    )
    db_session.add(role_to_update)
    db_session.commit()
    db_session.refresh(role_to_update, attribute_names=['permissions'])
    role_id_str = str(role_to_update.id)

    # Verify initial state
    assert len(role_to_update.permissions) == 2
    current_db_perm_ids = sorted([str(p.id) for p in role_to_update.permissions])
    assert current_db_perm_ids == initial_permission_ids

    # 4. Prepare update payload without 'permission_ids'
    updated_description = "Updated description, permissions should be same."
    update_payload = json.loads(RoleUpdate(
        name=role_name,
        description=updated_description
        # permission_ids is intentionally omitted for this test case
    ).model_dump_json(exclude_unset=True))

    # 5. Call PUT endpoint
    response = await authenticated_test_client.put(
        f"/api/v1/roles/{role_id_str}",
        json=update_payload
    )

    # 6. Assertions for PUT response
    assert response.status_code == status.HTTP_200_OK
    updated_role_data = response.json()
    assert updated_role_data["name"] == role_name
    assert updated_role_data["description"] == updated_description
    
    response_permission_ids = sorted([p['id'] for p in updated_role_data.get("permissions", [])])
    response_permission_names = sorted([p['name'] for p in updated_role_data.get("permissions", [])])
    
    assert response_permission_ids == initial_permission_ids
    assert response_permission_names == initial_permission_names


    # 7. Verify changes in the database
    # Re-fetch the role from the database to ensure we have the latest state
    # The original role_to_update object might be stale after the API call.
    role_id_uuid = uuid.UUID(role_id_str) # Convert string ID back to UUID object for querying
    
    # Fetch the role again, ensuring permissions are eagerly loaded.
    role_in_db_after_update = db_session.query(RoleModel).filter(RoleModel.id == role_id_uuid).options(selectinload(RoleModel.permissions)).one()
    
    assert role_in_db_after_update.description == updated_description, "Description was not updated correctly in the DB."
    
    final_db_perm_ids = sorted([str(p.id) for p in role_in_db_after_update.permissions])
    assert final_db_perm_ids == initial_permission_ids, "Permissions should not have changed in the DB."

    # Clean up
    # Use the freshly fetched instance for cleanup
    role_in_db_after_update.permissions = [] 
    db_session.commit() # Commit permission changes (clearing them)
    db_session.delete(role_in_db_after_update) # Delete the role
    db_session.delete(permission1_for_unchanged_test)
    db_session.delete(permission2_for_unchanged_test)
    db_session.commit()