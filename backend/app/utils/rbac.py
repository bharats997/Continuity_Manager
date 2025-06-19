from typing import List, Callable, Optional, Coroutine, Any # Ensure Any is here
import uuid

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer # Example, adjust if using a different scheme
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import get_async_db
from app.models.domain.users import User as UserModel
from app.models.domain.roles import Role as RoleModel # SQLAlchemy model for Role
from ..schemas.role import RoleName # Enum for RoleName
from app.apis import deps # For get_current_user_placeholder

# Dependency to get the current active user with their roles eagerly loaded
async def get_current_active_user_with_roles(
    current_user: UserModel = Depends(deps.get_current_active_user) 
) -> UserModel:
    """
    This dependency ensures that we are working with the currently authenticated user,
    who has been fetched via token and has their organization, roles, and permissions
    eagerly loaded by the deps.get_current_active_user dependency.
    
    This function now primarily serves as a pass-through for the already processed user,
    maintaining the function signature for existing dependencies that use it.
    """
    if not current_user:
        # This case should ideally be handled by deps.get_current_active_user raising an HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="RBAC: Current active user not available."
        )
    # The user from deps.get_current_active_user should already have roles and permissions loaded.
    return current_user

# Factory for a dependency that ensures the user has one of the specified roles
def ensure_user_has_roles(required_roles: List[RoleName]) -> Callable:
    async def role_checker(
        user_with_roles: Any = Depends(get_current_active_user_with_roles)
    ) -> UserModel:
        if not user_with_roles.roles: # Handles case where roles list is empty or None
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned roles."
            )
        
        # Extract the names of the roles the user has.
        # The 'name' attribute of the RoleModel (SQLAlchemy model) should store the role name string.
        user_role_names = {role.name for role in user_with_roles.roles if hasattr(role, 'name')}
        
        # Convert required RoleName enums to their string values for comparison.
        required_role_values = {role_enum.value for role_enum in required_roles}

        if not user_role_names.intersection(required_role_values):
            missing_roles_str = ", ".join(sorted(list(required_role_values)))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have the required roles. Access denied. Required: {missing_roles_str}."
            )
        return user_with_roles
    return role_checker

# Factory for a dependency that ensures the user has the specified permissions
def ensure_user_has_permissions(required_permissions: List[str]) -> Callable:
    async def permission_checker(
        user_with_roles: UserModel = Depends(get_current_active_user_with_roles) # UserModel is already defined as app.models.domain.users.User
    ) -> UserModel:
        if not user_with_roles.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned roles, and therefore no permissions."
            )

        user_permissions_set = set()
        for role_obj in user_with_roles.roles: # role_obj to avoid conflict
            if hasattr(role_obj, 'permissions') and role_obj.permissions:
                for perm_obj in role_obj.permissions: # perm_obj to avoid conflict
                    if hasattr(perm_obj, 'name'): # Assuming Permission model has a 'name' attribute
                        user_permissions_set.add(perm_obj.name)
        
        # Check if all required permissions are present
        missing_permissions = [
            p_name for p_name in required_permissions if p_name not in user_permissions_set
        ]

        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have the required permissions: {', '.join(sorted(missing_permissions))}."
            )
        return user_with_roles
    return permission_checker