import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

# App specific imports
from app.models.domain.users import User as UserModel
from app.models.domain.roles import Role as RoleModel
from app.models.domain.permissions import Permission as PermissionModel
from app.models.domain.organizations import Organization as OrganizationModel

# Define static UUIDs for default entities
DEFAULT_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
DEFAULT_ORG_NAME = "Default Test Organization"

async def _ensure_default_organization(session: AsyncSession, org_id: uuid.UUID, org_name: str = "Default Test Organization") -> OrganizationModel:
    stmt = select(OrganizationModel).where(OrganizationModel.id == org_id)
    result = await session.execute(stmt)
    org = result.scalars().first()
    if not org:
        # The default organization should always exist as it's seeded in conftest.py's db_connection fixture.
        # If it's not found here, something is wrong with the test setup.
        raise RuntimeError(
            f"Default organization with ID {org_id} not found. "
            f"It should have been seeded by the db_connection fixture in conftest.py."
        )
    return org

async def create_role_with_permissions_async(
    db_session: AsyncSession,
    role_name: str,
    permissions_names: List[str],
    organization_id: uuid.UUID
) -> RoleModel:
    await _ensure_default_organization(db_session, organization_id)
    role_permissions = []
    for p_name in permissions_names:
        stmt = select(PermissionModel).where(PermissionModel.name == p_name)
        result = await db_session.execute(stmt)
        permission = result.scalars().first()
        if not permission:
            permission = PermissionModel(name=p_name, description=f"Test permission {p_name}")
            db_session.add(permission)
            await db_session.flush() # Permission is in session, ID is populated
            await db_session.refresh(permission) # Ensure all attributes of the new permission are loaded
        role_permissions.append(permission)
    
    role = RoleModel(
        name=role_name,
        organization_id=organization_id,
        permissions=role_permissions # Assign the list of (hopefully) fully loaded PermissionModel instances
    )
    db_session.add(role)
    await db_session.flush() # Role is in session, ID is populated

    # Re-fetch the role with its permissions eagerly loaded to ensure the returned object is fully populated.
    role_id = role.id # Capture ID before potential expiry
    final_role_stmt = (
        select(RoleModel)
        .options(joinedload(RoleModel.permissions))
        .where(RoleModel.id == role_id)
    )
    result = await db_session.execute(final_role_stmt)
    refetched_role = result.scalars().unique().one_or_none()

    if refetched_role is None:
        raise RuntimeError(f"Failed to re-fetch role with ID {role_id} after creation.")
    
    return refetched_role

async def create_user_with_roles_async(
    db_session: AsyncSession,
    email: str,
    first_name: str,
    last_name: str,
    organization_id: uuid.UUID,
    role_names: List[str],
    is_active: bool = True,
    is_superuser: bool = False,
    hashed_password: str = "testpassword"
) -> UserModel:
    await _ensure_default_organization(db_session, organization_id)
    user_roles = []
    for r_name in role_names:
        stmt = select(RoleModel).options(joinedload(RoleModel.permissions)).where(RoleModel.name == r_name, RoleModel.organization_id == organization_id)
        result = await db_session.execute(stmt)
        role = result.scalars().first()
        if not role:
             raise ValueError(f"Role '{r_name}' not found in organization '{organization_id}'. Create it first.")
        user_roles.append(role)
    user = UserModel(
        email=email,
        first_name=first_name,
        last_name=last_name,
        organization_id=organization_id,
        password_hash=hashed_password,
        is_active=is_active,
        roles=user_roles
    )
    db_session.add(user)
    await db_session.flush() # User is in session, ID is populated

    # Re-fetch the user with roles and their permissions eagerly loaded.
    # This ensures the returned user object is fully populated for subsequent access
    # in tests/dependencies without triggering problematic lazy loads.
    user_id = user.id # Capture ID before potential expiry if session state changes
    final_user_stmt = (
        select(UserModel)
        .options(
            joinedload(UserModel.roles).joinedload(RoleModel.permissions)
        )
        .where(UserModel.id == user_id)
    )
    result = await db_session.execute(final_user_stmt)
    refetched_user = result.scalars().unique().one_or_none()
    if refetched_user is None:
        # This should ideally not happen if flush was successful and user_id is valid
        raise RuntimeError(f"Failed to re-fetch user with ID {user_id} after creation.")
    return refetched_user
