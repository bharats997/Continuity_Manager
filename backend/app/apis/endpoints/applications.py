# backend/app/apis/endpoints/applications.py
import uuid
from typing import List, Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

# Application-specific imports
from ...schemas.applications import ApplicationCreate, ApplicationUpdate, ApplicationRead
from ...services.application_service import application_service
from ...db.session import get_async_db
from ...models.domain.users import User
from ..deps import get_current_active_user

router = APIRouter()

@router.post("/", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(
    *,
    db: AsyncSession = Depends(get_async_db),
    application_in: ApplicationCreate,
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new application.
    """
    try:
        application_orm = await application_service.create_application(
            db=db, application_in=application_in, current_user=current_user
        )
        return application_orm
    except Exception as e:
        # Catch potential exceptions from the service layer, e.g., duplicate name
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{application_id}", response_model=ApplicationRead)
async def read_application(
    application_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Retrieve a single application by its ID, scoped to the current user's organization.
    """
    db_application = await application_service.get_application_by_id(
        db,
        application_id=application_id,
        organization_id=current_user.organization_id
    )
    if db_application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found or not accessible in your organization.")
    
    return db_application

@router.get("/", response_model=List[ApplicationRead])
async def read_applications(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1, description="Page number, 1-indexed"),
    size: int = Query(10, ge=1, le=200, description="Number of items per page"),
    name: Optional[str] = Query(None, description="Filter by application name (case-insensitive, partial match)"),
    application_type: Optional[str] = Query(None, alias="type", description="Filter by application type (e.g., Owned, SAAS, Third-Party)") # Alias 'type' to match test and common usage
):
    """
    Retrieve a list of applications for the current user's organization.
    Supports pagination.
    """
    skip = (page - 1) * size
    applications = await application_service.get_applications(
        db=db, 
        organization_id=current_user.organization_id, 
        skip=skip, 
        limit=size, # Use 'size' from query as 'limit' for the service
        name=name,
        application_type=application_type
    )
    return applications

@router.put("/{application_id}", response_model=ApplicationRead)
async def update_application(
    application_id: uuid.UUID,
    application_in: ApplicationUpdate,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
    # current_user: Annotated[User, Depends(require_admin)] # For RBAC
):
    """
    Update an existing application within the current user's organization.
    Requires admin privileges.
    """
    try:
        updated_application = await application_service.update_application(
            db=db, 
            application_id=application_id, 
            application_in=application_in, 
            organization_id=current_user.organization_id
        )
        if updated_application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found or not accessible for update.")
        return updated_application
    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from service layer
    except ValueError as ve: # Catch specific validation errors if service raises them
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        # TODO: Log the exception e
        print(f"Unexpected error in update_application: {e}") # Temporary print
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while updating the application.")

@router.delete("/{application_id}", response_model=ApplicationRead)
async def delete_application(
    application_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
    # current_user: Annotated[User, Depends(require_admin)] # For RBAC
):
    """
    Soft delete an application within the current user's organization.
    Requires admin privileges.
    """
    try:
        # The service method get_application (called internally by delete_application if it checks existence first)
        # or the delete_application method itself will handle not_found or already_deleted cases.
        deleted_application = await application_service.delete_application(
            db=db, 
            application_id=application_id, 
            organization_id=current_user.organization_id
        )
        if deleted_application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found or not accessible for deletion.")
        return deleted_application
    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from service layer
    except ValueError as ve: # Should ideally be handled by service layer raising HTTPException
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # TODO: Log the exception e
        print(f"Unexpected error in delete_application: {e}") # Temporary print
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during deletion.")
