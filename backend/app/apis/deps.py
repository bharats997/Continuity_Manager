# backend/app/apis/deps.py
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload

from ..database.session import SessionLocal
# Assuming a simplified User model for current_user for now
# In a real app, this would come from your auth system (e.g., JWT decoding)
from ..models.person import Person as UserSchema # Using Person Pydantic model as a placeholder
from ..models.domain.people import Person as PersonDB # SQLAlchemy model
from ..services.person_service import person_service

# Placeholder for OAuth2 scheme if you use token-based auth
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Adjust tokenUrl as needed

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Placeholder for Current User ---
# This is a simplified version. In a real app, you'd decode a token
# and fetch the user from the DB.
async def get_current_user_placeholder(
    db: Session = Depends(get_db),
    # token: str = Depends(oauth2_scheme) # Uncomment if using token auth
    # For now, let's simulate a user, e.g., user with ID 1 from org 1
    # This MUST be replaced with actual authentication
    simulated_user_id: int = 1, # Example: User ID 1
    simulated_organization_id: int = 1 # Example: Org ID 1
) -> PersonDB: # Returning SQLAlchemy model
    print(f"DEBUG [deps.py get_current_user_placeholder]: Entered. DB session object ID: {id(db)}")
    # In a real scenario, you'd decode a token to get user_id and organization_id
    # and then fetch the user.
    # ---- DEBUG PRINT START ----
    print(f"DEBUG [deps.py]: Attempting to fetch user with person_id={simulated_user_id}, organization_id={simulated_organization_id} using db session: {db}")
    # ---- DETAILED DEBUG PRINT START ----
    user_initial_fetch = person_service.get_person_by_id(db, person_id=simulated_user_id, organization_id=simulated_organization_id)

    if user_initial_fetch:
        print(f"DEBUG [deps.py get_current_user_placeholder]: User initially fetched. Object ID: {id(user_initial_fetch)}")
        # Re-fetch the user with the current session (db) and explicitly load organization
        # to ensure it's bound to this session and avoid DetachedInstanceError.
        user = (
            db.query(PersonDB)
            .options(joinedload(PersonDB.organization))
            .filter(PersonDB.id == user_initial_fetch.id)
            .first()
        )
        if user:
            print(f"DEBUG [deps.py get_current_user_placeholder]: User re-fetched/merged. Object ID: {id(user)}")
        else:
            # This should ideally not happen if user_initial_fetch was successful
            print(f"DEBUG [deps.py get_current_user_placeholder]: User re-fetch failed!")
            user = None # Explicitly set to None if re-fetch fails
    else:
        user = None
        print(f"DEBUG [deps.py get_current_user_placeholder]: Initial user fetch failed.")

    # ---- DETAILED DEBUG PRINT START ----
    if user:
        print(f"DEBUG [deps.py get_current_user_placeholder]: User object ID: {id(user)}, Email: {user.email}")
        try:
            # Attempt to access related organization to see if it triggers issues
            if user.organizationId == 1: # Only try for default org for this specific debug
                org_instance = user.organization # Access the relationship
                if org_instance:
                    print(f"DEBUG [deps.py get_current_user_placeholder]: Accessed user.organization (ID: {org_instance.id}, Name: {org_instance.name}). Object ID: {id(org_instance)}")
                else:
                    print(f"DEBUG [deps.py get_current_user_placeholder]: user.organization is None even after access.")
            else:
                print(f"DEBUG [deps.py get_current_user_placeholder]: User's organizationId is not 1, not printing organization details.")
        except Exception as e_org_access:
            print(f"DEBUG [deps.py get_current_user_placeholder]: Error accessing user.organization: {type(e_org_access).__name__}: {e_org_access}")
    else:
        print(f"DEBUG [deps.py get_current_user_placeholder]: User not found by person_service.")
    # ---- DETAILED DEBUG PRINT END ----
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # For this placeholder, we assume it's part of the user object or can be derived.
    # setattr(user, 'organizationId', simulated_organization_id) # Ensure org ID is accessible
    return user

# --- RBAC Dependencies ---

# For Department Management (FR 1.1)
def allow_department_management(current_user: PersonDB = Depends(get_current_user_placeholder)):
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

# For People Management (FR 1.2) - Typically Admin only
def allow_people_management(current_user: PersonDB = Depends(get_current_user_placeholder)):
    allowed_roles = {"Admin"}
    user_role_names = {role.name for role in current_user.roles}
    if not allowed_roles.intersection(user_role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage people."
        )
    return current_user

# For general read access to people/roles (e.g., by BCM Managers or Department Heads)
def allow_people_read(current_user: PersonDB = Depends(get_current_user_placeholder)):
    # More permissive: Admin, BCM Manager, Department Head might need to see people lists
    allowed_roles = {"Admin", "BCM Manager", "Department Head"}
    user_role_names = {role.name for role in current_user.roles}
    if not allowed_roles.intersection(user_role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this information."
        )
    return current_user

# Dependency to get current active user (can be used by any authenticated user for their own info)
async def get_current_active_user(
    current_user: PersonDB = Depends(get_current_user_placeholder),
) -> PersonDB:
    if not current_user.isActive:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

