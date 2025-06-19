import asyncio
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal  # Changed import
from app.models.domain.roles import Role as RoleModel
from app.models.domain.users import User as UserModel
from app.models.domain.organizations import Organization as OrganizationModel
from app.models.domain.permissions import Permission as PermissionModel
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEFAULT_ORG_NAME = "Default Organization"

DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "SecurePassword123!"
DEFAULT_ADMIN_FULL_NAME = "Default Admin User"

PREDEFINED_ROLES = [
    {"name": "Admin", "description": "System Administrator with full access."},
    {"name": "BCM Manager", "description": "Business Continuity Management Program Manager."},
    {"name": "CISO", "description": "Chief Information Security Officer."},
    {"name": "Department Head", "description": "Head of a specific department."},
    {"name": "Internal Auditor", "description": "Audits BCMS processes and compliance."},
    {"name": "Process Owner", "description": "Owner of specific business processes."},
    {"name": "Standard User", "description": "Standard user with basic access."}
]

BIA_CATEGORY_PERMISSIONS_DATA = [
    {"name": "bia_category_create", "description": "Allows creating BIA categories."},
    {"name": "bia_category_read", "description": "Allows reading BIA categories."},
    {"name": "bia_category_update", "description": "Allows updating BIA categories."},
    {"name": "bia_category_delete", "description": "Allows deleting BIA categories."},
]

BIA_PARAMETER_PERMISSIONS_DATA = [
    {"name": "bia_parameter:create", "description": "Allows creating BIA parameters (scales and timeframes)."},
    {"name": "bia_parameter:read", "description": "Allows reading BIA parameters."},
    {"name": "bia_parameter:update", "description": "Allows updating BIA parameters."},
    {"name": "bia_parameter:delete", "description": "Allows deleting BIA parameters."},
    {"name": "bia_parameter:list", "description": "Allows listing BIA parameters."},
]


# Define which roles get which permissions
ROLE_PERMISSION_ASSIGNMENTS = {
    "Admin": [
        "bia_category_create", "bia_category_read", "bia_category_update", "bia_category_delete",
        "bia_parameter:create", "bia_parameter:read", "bia_parameter:update", "bia_parameter:delete", "bia_parameter:list",
    ],
    "BCM Manager": [
        "bia_category_create", "bia_category_read", "bia_category_update", "bia_category_delete",
        "bia_parameter:create", "bia_parameter:read", "bia_parameter:update", "bia_parameter:delete", "bia_parameter:list",
    ],
    "CISO": [
        "bia_category_create", "bia_category_read", "bia_category_update", "bia_category_delete",
        "bia_parameter:create", "bia_parameter:read", "bia_parameter:update", "bia_parameter:delete", "bia_parameter:list",
    ],
    "Internal Auditor": [
        "bia_category_read",
        "bia_parameter:read",
        "bia_parameter:list",
    ]
}

async def seed_roles(db: AsyncSession, organization_id: uuid.UUID) -> dict[str, RoleModel]:
    created_roles = {}
    logger.info("Seeding predefined roles...")
    for role_data in PREDEFINED_ROLES:
        stmt = select(RoleModel).where(RoleModel.name == role_data["name"], RoleModel.organization_id == organization_id).options(selectinload(RoleModel.permissions))
        result = await db.execute(stmt)
        existing_role = result.scalars().first()

        if not existing_role:
            new_role = RoleModel(name=role_data["name"], description=role_data["description"], organization_id=organization_id)
            db.add(new_role)
            await db.flush() # Flush to get ID if needed immediately
            created_roles[new_role.name] = new_role
            logger.info(f"Role '{new_role.name}' created.")
        else:
            created_roles[existing_role.name] = existing_role
            logger.info(f"Role '{existing_role.name}' already exists.")
    await db.commit()
    logger.info("Role seeding finished.")
    return created_roles


async def seed_permissions(db: AsyncSession) -> dict[str, PermissionModel]:
    created_permissions = {}
    logger.info("Seeding permissions...")
    all_permissions_data = BIA_CATEGORY_PERMISSIONS_DATA + BIA_PARAMETER_PERMISSIONS_DATA

    for perm_data in all_permissions_data:
        stmt = select(PermissionModel).where(PermissionModel.name == perm_data["name"])
        result = await db.execute(stmt)
        existing_permission = result.scalars().first()

        if not existing_permission:
            new_permission = PermissionModel(name=perm_data["name"], description=perm_data["description"])
            db.add(new_permission)
            await db.flush() # Flush to get ID if needed
            created_permissions[new_permission.name] = new_permission
            logger.info(f"Permission '{new_permission.name}' created.")
        else:
            created_permissions[existing_permission.name] = existing_permission
            logger.info(f"Permission '{existing_permission.name}' already exists.")
    await db.commit() # Commit after adding all new permissions
    logger.info("Permission seeding finished.")
    return created_permissions


async def assign_permissions_to_roles(
    db: AsyncSession, 
    seeded_roles: dict[str, RoleModel],
    seeded_permissions: dict[str, PermissionModel]
):
    logger.info("Assigning permissions to roles...")
    for role_name, permission_names in ROLE_PERMISSION_ASSIGNMENTS.items():
        role_obj = seeded_roles.get(role_name)
        if not role_obj:
            logger.warning(f"Role '{role_name}' not found in seeded_roles. Skipping permission assignment.")
            continue

        for perm_name in permission_names:
            perm_obj = seeded_permissions.get(perm_name)
            if not perm_obj:
                logger.warning(f"Permission '{perm_name}' not found in seeded_permissions. Skipping assignment to role '{role_name}'.")
                continue
            
            # Check if permission is already associated
            if perm_obj not in role_obj.permissions:
                role_obj.permissions.append(perm_obj)
                logger.info(f"Assigned permission '{perm_name}' to role '{role_name}'.")
            else:
                logger.info(f"Permission '{perm_name}' already assigned to role '{role_name}'.")
    
    await db.commit() # Commit changes to role_permissions association
    logger.info("Permission assignment to roles finished.")


async def get_or_create_default_organization(db: AsyncSession) -> OrganizationModel:
    logger.info(f"Checking for default organization: {DEFAULT_ORG_NAME} (ID: {DEFAULT_ORG_ID})")
    org = await db.get(OrganizationModel, DEFAULT_ORG_ID)
    if not org:
        logger.info(f"Default organization not found. Creating...")
        org = OrganizationModel(id=DEFAULT_ORG_ID, name=DEFAULT_ORG_NAME, description="Default organization for the system.")
        db.add(org)
        await db.commit()
        await db.refresh(org)
        logger.info(f"Default organization '{org.name}' created with ID {org.id}.")
    else:
        logger.info(f"Default organization '{org.name}' found.")
    return org

async def get_or_create_default_admin(db: AsyncSession, organization: OrganizationModel, admin_role: RoleModel) -> UserModel:
    logger.info(f"Checking for default admin user: {DEFAULT_ADMIN_EMAIL}")
    stmt = select(UserModel).where(UserModel.email == DEFAULT_ADMIN_EMAIL).options(selectinload(UserModel.roles))
    result = await db.execute(stmt)
    admin_user = result.scalars().first()

    if not admin_user:
        logger.info(f"Default admin user not found. Creating...")
        password_hash = get_password_hash(DEFAULT_ADMIN_PASSWORD)
        admin_user = UserModel(
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=password_hash,
            first_name="Admin",
            last_name="User",
            organization_id=organization.id,
            is_active=True,
                    )
        admin_user.roles.append(admin_role) # Assign the admin role
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
        logger.info(f"Default admin user '{admin_user.email}' created.")
    else:
        logger.info(f"Default admin user '{admin_user.email}' found.")
        # Ensure admin role is assigned if user exists but role is missing
        if admin_role not in admin_user.roles:
            admin_user.roles.append(admin_role)
            await db.commit()
            logger.info(f"Assigned Admin role to existing user '{admin_user.email}'.")
    return admin_user

async def init_db():
    session: AsyncSession = AsyncSessionLocal()
    try:
        logger.info("Starting database initialization and seeding...")
        default_org = await get_or_create_default_organization(session)
        seeded_roles = await seed_roles(session, default_org.id) # Pass organization_id
        seeded_permissions = await seed_permissions(session)
        await assign_permissions_to_roles(session, seeded_roles, seeded_permissions)
        
        admin_role_name = "Admin"
        admin_role = seeded_roles.get(admin_role_name)
        
        if not admin_role:
            # Attempt to fetch from DB again if not in created_roles (e.g. if it already existed)
            stmt = select(RoleModel).where(RoleModel.name == admin_role_name)
            result = await session.execute(stmt)
            admin_role = result.scalars().first()

        if not admin_role:
            logger.error(f"'{admin_role_name}' role not found or created. Cannot create default admin user.")
            # Optionally, create it here if absolutely critical and missed by seed_roles
            # For now, we'll just error out
            return

        await get_or_create_default_admin(session, default_org, admin_role) # This function also handles its own commit
        
        # A final commit in init_db might be redundant if all sub-functions commit,
        # but can be useful if there were direct db.add() operations here.
        # await session.commit() # Ensure any pending changes from this scope are committed (if any)
        logger.info("Database initialization and seeding process completed successfully.")
    except Exception as e:
        await session.rollback() # Rollback in case of error during the process
        logger.error(f"An error occurred during database initialization: {e}", exc_info=True)
        # Re-raise the exception if you want the script to exit with an error code
        raise 
    finally:
        await session.close()
        logger.info("Database session closed.")

if __name__ == "__main__":
    logger.info("Starting database initialization script...")
    asyncio.run(init_db())
