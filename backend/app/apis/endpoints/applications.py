# backend/app/apis/endpoints/applications.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...services.application_service import application_service
from ...models.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from ...models.domain.people import Person as PersonDomain # For current_user dependency
from ..deps import get_db, get_current_active_user

router = APIRouter()

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    application_in: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: PersonDomain = Depends(get_current_active_user)
):
    """
    Create a new application.
    - `organizationId` must be provided in the request body.
    - `appOwnerId` is optional.
    - Creator and updater will be set to the current authenticated user.
    """
    try:
        # Authorization: Ensure current_user has rights to create an application for the given organizationId
        # This might involve checking if current_user.organizationId matches application_in.organizationId
        # or if the user has a specific role/permission.
        # For now, we assume the service layer or a higher level handles this if necessary.
        # if current_user.organizationId != application_in.organizationId:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="You do not have permission to create applications for this organization."
        #     )
        
        created_application = application_service.create_application(
            db=db, application_in=application_in, creator_id=current_user.id
        )
        return created_application
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

@router.get("/{application_id}", response_model=ApplicationResponse)
def read_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: PersonDomain = Depends(get_current_active_user) # For authorization if needed
):
    """
    Retrieve a single application by its ID.
    """
    db_application = application_service.get_application(db, application_id=application_id)
    if db_application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    
    # Authorization: Check if current_user has permission to view this application
    # (e.g., if it belongs to their organization)
    # if db_application.organizationId != current_user.organizationId:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this application")
    return db_application

@router.get("/", response_model=List[ApplicationResponse])
def read_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    organization_id: Optional[int] = Query(None, description="Filter applications by organization ID"),
    db: Session = Depends(get_db),
    current_user: PersonDomain = Depends(get_current_active_user)
):
    """
    Retrieve a list of applications.
    - Supports pagination with `skip` and `limit`.
    - Can be filtered by `organization_id`.
    - By default, only shows applications for the current user's organization if organization_id is not specified
      (This logic can be enforced here or in the service layer).
    """
    # If organization_id is not provided, default to current_user's organizationId for non-admin users
    # This is a common authorization pattern. Adjust as per your RBAC requirements.
    # if organization_id is None and not current_user.is_superuser: # Assuming an is_superuser flag or role check
    #     effective_organization_id = current_user.organizationId
    # else:
    effective_organization_id = organization_id

    applications = application_service.get_applications(
        db, skip=skip, limit=limit, organization_id=effective_organization_id
    )
    return applications

@router.put("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    application_in: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: PersonDomain = Depends(get_current_active_user)
):
    """
    Update an existing application.
    """
    db_application = application_service.get_application(db, application_id=application_id)
    if db_application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    # Authorization: Check if current_user has permission to update this application
    # (e.g., if it belongs to their organization or they are an admin/app owner)
    # if db_application.organizationId != current_user.organizationId and not current_user.is_superuser:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this application")

    try:
        updated_application = application_service.update_application(
            db=db, application_id=application_id, application_in=application_in, updater_id=current_user.id
        )
        return updated_application
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during update.")

@router.delete("/{application_id}", response_model=ApplicationResponse)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: PersonDomain = Depends(get_current_active_user)
):
    """
    Soft delete an application.
    """
    db_application = application_service.get_application(db, application_id=application_id)
    if db_application is None:
        # To make delete idempotent, you might return 204 No Content or the (already deleted) object
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    # Authorization: Check if current_user has permission to delete this application
    # if db_application.organizationId != current_user.organizationId and not current_user.is_superuser:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this application")
    
    try:
        # The service method get_application already filters by deletedAt.is_(None)
        # If it was found, it means it's not yet deleted.
        deleted_application = application_service.delete_application(
            db=db, application_id=application_id, deleter_id=current_user.id
        )
        if deleted_application is None: # Should not happen if found above, but as a safeguard
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found or error during deletion")
        return deleted_application
    except ValueError as ve: # e.g., if service raises an error like "already deleted"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during deletion.")
