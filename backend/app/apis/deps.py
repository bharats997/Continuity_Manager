# backend/app/apis/deps.py
import uuid # Added import
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import selectinload # Changed from joinedload for consistency, though selectinload is already used below
from jose import JWTError, jwt
from app.config import settings
from app.schemas.token_schemas import TokenPayload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..db.session import get_async_db
# Assuming a simplified User model for current_user for now
# In a real app, this would come from your auth system (e.g., JWT decoding)
from ..schemas.user_schemas import UserSchema # Using User Pydantic model
from ..models.domain.users import User as UserDB # SQLAlchemy model
from ..models.domain.roles import Role as RoleDB # Import RoleDB for joinedload
from ..services.user_service import user_service

# --- Permission Constants ---
class DepartmentPermissions:
    CREATE = "department:create"
    READ = "department:read"
    UPDATE = "department:update"
    DELETE = "department:delete"
    LIST = "department:list"

class RolePermissions:
    CREATE = "role:create"
    READ = "role:read"
    UPDATE = "role:update"
    DELETE = "role:delete"
    LIST = "role:list"
    ASSIGN_PERMISSIONS = "role:assign_permissions"

class UserPermissions: # Renamed from PersonPermissions
    CREATE = "user:create"
    READ = "user:read"
    UPDATE = "user:update"
    DELETE = "user:delete"
    LIST = "user:list"

class LocationPermissions:
    CREATE = "location:create"
    READ = "location:read"
    UPDATE = "location:update"
    DELETE = "location:delete"
    LIST = "location:list"

class ApplicationPermissions:
    CREATE = "application:create"
    READ = "application:read"
    UPDATE = "application:update"
    DELETE = "application:delete"
    LIST = "application:list"

class ProcessPermissions:
    CREATE = "process:create"
    READ = "process:read"
    UPDATE = "process:update"
    DELETE = "process:delete"
    LIST = "process:list"

class BIAParameterPermissions:
    CREATE = "bia_parameter:create"
    READ = "bia_parameter:read"
    UPDATE = "bia_parameter:update"
    DELETE = "bia_parameter:delete"
    LIST = "bia_parameter:list"

class OrganizationPermissions:
    READ = "organization:read"
    UPDATE = "organization:update"
    LIST_USERS = "organization:list_users" # Example specific permission
    # Typically, creating/deleting organizations is a super-admin task outside general RBAC

# Consider adding a helper to get all defined permission names if needed for seeding/admin UI
ALL_DEFINED_PERMISSIONS = []
for perm_enum in [DepartmentPermissions, RolePermissions, UserPermissions, LocationPermissions, ApplicationPermissions, ProcessPermissions, BIAParameterPermissions, OrganizationPermissions]:
    for member_name, member_value in vars(perm_enum).items():
        if not member_name.startswith('_') and isinstance(member_value, str):
            ALL_DEFINED_PERMISSIONS.append(member_value)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# --- Token-based Current User ---

# Define static UUIDs for the placeholder's default simulated user and organization
# These match the DEFAULT_USER_ID and DEFAULT_ORG_ID in conftest.py for consistent behavior
# when the placeholder is active (e.g., if tests use unauthenticated client by mistake for auth'd endpoints)
DEFAULT_PLACEHOLDER_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEFAULT_PLACEHOLDER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")

# This is a simplified version. In a real app, you'd decode a token
# and fetch the user from the DB.
async def get_current_user_from_token(
    db: AsyncSession = Depends(get_async_db),
    token: str = Depends(oauth2_scheme)
) -> UserDB:
    """
    Decodes the JWT token to extract user and organization identifiers, then fetches
    the user from the database.
    It eagerly loads the user's roles and permissions to prevent async lazy loading issues.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        if token_data.sub is None or token_data.organization_id is None:
            logger.error("Token is missing 'sub' or 'organization_id' fields.")
            raise credentials_exception

        # Convert string UUIDs from token back to UUID objects
        user_id = uuid.UUID(token_data.sub)
        organization_id = uuid.UUID(token_data.organization_id)

    except (JWTError, ValueError) as e:
        logger.error(f"Token validation failed: {e}")
        raise credentials_exception

    user = await user_service.get_user_by_id(db, user_id=user_id, organization_id=organization_id)
    
    if user is None:
        logger.warning(f"User with ID '{user_id}' not found in organization '{organization_id}'.")
        raise credentials_exception

    return user

# Dependency to get current active user (can be used by any authenticated user for their own info)
async def get_current_active_user(
    current_user: UserDB = Depends(get_current_user_from_token),
) -> UserDB:
    print(f"DEBUG [deps.py get_current_active_user]: Entered for user {current_user.email if current_user else 'None'}")
    if current_user:
        print(f"DEBUG [deps.py get_current_active_user]: User is_active: {current_user.is_active}")
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    print(f"DEBUG [deps.py get_current_active_user]: Returning active user.")
    return current_user

# --- RBAC Dependencies ---
# For Department Management (FR 1.1)
def allow_department_management(current_user: UserDB = Depends(get_current_active_user)):
    # Check if the user has 'Admin' or 'BCM Manager' role
    # This assumes current_user.roles is a list of Role objects with a 'name' attribute
    allowed_roles = {"Admin", "BCM Manager"}
    user_role_names = {role.name for role in current_user.roles}
    if not allowed_roles.intersection(user_role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage departments."
        )
    return current_user

# --- New Permission-Based RBAC Dependency ---
def RequirePermission(permission_name: str):
    """
    Dependency factory that creates a dependency to check for a specific permission.
    """
    async def permission_checker(current_user: UserDB = Depends(get_current_active_user)) -> UserDB:
        user_permissions = {perm.name for role in current_user.roles if role and role.permissions for perm in role.permissions if perm and perm.name}
        if permission_name in user_permissions:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )  
    return permission_checker

# For User Management (FR 1.2) - Typically Admin only
def allow_user_management(current_user: UserDB = Depends(get_current_active_user)): 
    allowed_roles = {"Admin"}
    user_role_names = {role.name for role in current_user.roles}
    if not allowed_roles.intersection(user_role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage users."
        )
    return current_user

# For general read access to users/roles (e.g., by BCM Managers or Department Heads)
def allow_user_read(current_user: UserDB = Depends(get_current_active_user)): 
    # More permissive: Admin, BCM Manager, Department Head might need to see user lists
    allowed_roles = {"Admin", "BCM Manager", "Department Head"}
    user_role_names = {role.name for role in current_user.roles}
    if not allowed_roles.intersection(user_role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this information."
        )
    return current_user

