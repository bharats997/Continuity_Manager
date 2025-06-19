# backend/app/apis/endpoints/processes.py
import uuid
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import get_async_db as get_db_session, get_current_active_user, RequirePermission, ProcessPermissions
from ...schemas.user_schemas import UserSchema as CurrentUserSchema # For current user dependency
from ...schemas.processes import ProcessCreate, ProcessUpdate, ProcessResponse, ProcessListResponse
from ...services.process_service import ProcessService
from ...services.process_service import NotFoundException, BadRequestException, DatabaseException, ConflictException

router = APIRouter()

@router.post(
    "/",
    response_model=ProcessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Business Process",
    description="Creates a new business process within the user's organization."
)
async def create_process(
    process_in: ProcessCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: CurrentUserSchema = Depends(RequirePermission(ProcessPermissions.CREATE))
):
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organization."
        )
    
    process_service = ProcessService(db)
    try:
        created_process = await process_service.create_process(
            process_data=process_in,
            current_user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        return created_process
    except BadRequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundException as e: # For related entities not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        # Log the exception e (e.g., using a proper logger)
        # logger.error(f"UNEXPECTED ERROR in create_process: {type(e).__name__} - {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the process.")

@router.get(
    "/{process_id}",
    response_model=ProcessResponse,
    summary="Get a Business Process by ID",
    description="Retrieves a specific business process by its ID, if it belongs to the user's organization."
)
async def get_process(
    process_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: CurrentUserSchema = Depends(RequirePermission(ProcessPermissions.READ))
):
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organization."
        )

    process_service = ProcessService(db)
    try:
        process = await process_service.get_process_by_id(
            process_id=process_id,
            organization_id=current_user.organization_id
        )
        return process
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving the process.")

@router.get(
    "/",
    response_model=ProcessListResponse,
    summary="List Business Processes",
    description="Retrieves a list of business processes for the user's organization, with pagination, sorting, and filtering."
)
async def list_processes(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of items to return per page"),
    sort_by: Optional[str] = Query(None, description="Field name to sort by (e.g., 'name', 'created_at')"),
    sort_order: Optional[str] = Query("asc", description="Sort order: 'asc' or 'desc'"),
    db: AsyncSession = Depends(get_db_session),
    current_user: CurrentUserSchema = Depends(RequirePermission(ProcessPermissions.LIST))
):
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organization."
        )

    process_service = ProcessService(db)
    try:
        processes_db = await process_service.get_all_processes(
            organization_id=current_user.organization_id,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        total_processes = await process_service.count_processes(organization_id=current_user.organization_id)
        
        # Convert database objects to ProcessResponse objects
        # Pydantic's ProcessResponse will handle the serialization of individual items.
        # If ProcessListResponse expects List[ProcessResponse], Pydantic will handle coercion from dicts if necessary.
        response_items = [ProcessResponse.model_validate(p) for p in processes_db]

        return ProcessListResponse(
            items=response_items,
            total=total_processes,
            page=(skip // limit) + 1 if limit > 0 else 1,
            size=limit
        )
    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while listing processes.")

@router.put(
    "/{process_id}",
    response_model=ProcessResponse,
    summary="Update a Business Process",
    description="Updates an existing business process by its ID, if it belongs to the user's organization."
)
async def update_process(
    process_id: uuid.UUID,
    process_in: ProcessUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: CurrentUserSchema = Depends(RequirePermission(ProcessPermissions.UPDATE))
):
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organization."
        )

    process_service = ProcessService(db)
    try:
        updated_process = await process_service.update_process(
            process_id=process_id,
            process_data=process_in,
            current_user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        return updated_process
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BadRequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while updating the process.")

@router.delete(
    "/{process_id}",
    response_model=ProcessResponse, # Or status_code=204 if no content is returned
    summary="Delete a Business Process (Soft Delete)",
    description="Soft deletes a business process by its ID, if it belongs to the user's organization."
)
async def delete_process(
    process_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: CurrentUserSchema = Depends(RequirePermission(ProcessPermissions.DELETE))
):
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organization."
        )

    process_service = ProcessService(db)
    try:
        deleted_process = await process_service.delete_process(
            process_id=process_id,
            current_user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        # If delete_process returns None or raises an error for already deleted, 
        # this will be handled by exception blocks or by returning the object.
        return deleted_process
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while deleting the process.")
