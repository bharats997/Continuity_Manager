# backend/app/tests/api/test_roles_api.py
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from fastapi import status

from backend.app.models.domain.roles import Role as RoleModel
from backend.app.models.domain.people import Person as PersonModel, people_roles_association
from backend.app.models.role import Role as RoleSchema # Pydantic schema for response

# Helper to setup user with a specific role (adapted from test_people_api.py)
def setup_test_user_with_specific_role(db: Session, role_name: str, role_description: str = "Test role") -> tuple[PersonModel, RoleModel]:
    role = db.query(RoleModel).filter(RoleModel.name == role_name).first()
    if not role:
        role = RoleModel(name=role_name, description=role_description)
        db.add(role)
        db.flush() # Get role.id

    default_user = db.query(PersonModel).filter(PersonModel.id == 1).first()
    if not default_user:
        raise Exception("Default user (ID 1) not found in test setup.")

    is_role_assigned = any(assigned_role.id == role.id for assigned_role in default_user.roles)
    
    if not is_role_assigned:
        stmt = people_roles_association.insert().values(personId=default_user.id, roleId=role.id)
        db.execute(stmt)
        db.commit()
        db.refresh(default_user, attribute_names=['roles'])
    return default_user, role

# Helper to create predefined roles for testing
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
            role = RoleModel(name=name, description=description)
            db.add(role)
        created_roles[name] = role
    db.commit()
    # Refresh to ensure IDs are populated if newly created
    for role_obj in created_roles.values():
        if role_obj in db.dirty or role_obj in db.new: # Check if object is new or changed
             db.flush() # Flush to get ID if it was new
        db.refresh(role_obj) # Ensure it's up-to-date from DB
    return created_roles

@pytest.mark.asyncio
async def test_list_roles_as_bcm_manager(
    test_client: AsyncClient, 
    db_session: Session
):
    # Setup: Create predefined roles and assign 'BCM Manager' to default user
    predefined_roles = create_predefined_roles(db_session)
    bcm_manager_user, _ = setup_test_user_with_specific_role(db_session, "BCM Manager")

    response = await test_client.get("/api/v1/roles/")

    assert response.status_code == status.HTTP_200_OK
    roles_list = response.json()
    
    assert len(roles_list) == len(predefined_roles)
    
    # Verify structure and content (names are unique)
    response_role_names = {role['name'] for role in roles_list}
    expected_role_names = set(predefined_roles.keys())
    assert response_role_names == expected_role_names

    for role_data in roles_list:
        assert "id" in role_data
        assert "name" in role_data
        assert "description" in role_data
        assert role_data["name"] in predefined_roles
        assert role_data["description"] == predefined_roles[role_data["name"]].description

@pytest.mark.asyncio
async def test_get_role_by_id_as_bcm_manager(
    test_client: AsyncClient, 
    db_session: Session
):
    predefined_roles = create_predefined_roles(db_session)
    bcm_manager_user, _ = setup_test_user_with_specific_role(db_session, "BCM Manager")

    admin_role_db = predefined_roles["Admin"]
    
    response = await test_client.get(f"/api/v1/roles/{admin_role_db.id}")
    
    assert response.status_code == status.HTTP_200_OK
    role_data = response.json()
    
    assert role_data["id"] == admin_role_db.id
    assert role_data["name"] == admin_role_db.name
    assert role_data["description"] == admin_role_db.description

@pytest.mark.asyncio
async def test_get_role_not_found(
    test_client: AsyncClient, 
    db_session: Session
):
    # Ensure user is authorized to attempt the read
    create_predefined_roles(db_session) # Create roles so DB isn't empty
    setup_test_user_with_specific_role(db_session, "BCM Manager")
    
    non_existent_role_id = 99999
    response = await test_client.get(f"/api/v1/roles/{non_existent_role_id}")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Role not found"
