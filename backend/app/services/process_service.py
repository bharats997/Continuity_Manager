# backend/app/services/process_service.py
import uuid
from typing import List, Optional, Sequence

from sqlalchemy import select, update as sqlalchemy_update, delete as sqlalchemy_delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime # Added for deleted_at timestamp

from ..models.domain.processes import Process as ProcessModel, process_locations_association, process_applications_association, process_dependencies_association
from ..models.domain.users import User as UserModel
from fastapi import HTTPException # Added for specific exception handling
from ..models.domain.departments import Department as DepartmentModel
from ..models.domain.locations import Location as LocationModel
from ..models.domain.applications import Application as ApplicationModel

from ..schemas.processes import ProcessCreate, ProcessUpdate, ProcessResponse
class AppException(Exception):
    """Base class for application-specific exceptions."""
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)

class NotFoundException(AppException):
    """Raised when a resource is not found."""
    pass

class BadRequestException(AppException):
    """Raised for bad client requests (e.g., validation errors)."""
    pass

class DatabaseException(AppException):
    """Raised for database-related errors."""
    pass

class ForbiddenException(AppException):
    """Raised when an action is forbidden for the current user."""
    pass

class UnprocessableEntityException(AppException):
    """Raised when a request is well-formed but cannot be processed."""
    pass

class ConflictException(AppException):
    """Raised when a request conflicts with the current state of the target resource (e.g., duplicate)."""
    pass

class ProcessService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def _get_department_if_valid(self, department_id: uuid.UUID, organization_id: uuid.UUID) -> DepartmentModel:
        stmt = select(DepartmentModel).options(selectinload(DepartmentModel.locations)).where(DepartmentModel.id == department_id, DepartmentModel.organization_id == organization_id, DepartmentModel.is_deleted == False)
        result = await self.db_session.execute(stmt)
        department = result.scalars().first()
        if not department:
            raise NotFoundException(f"Department with ID {department_id} not found in your organization or has been deleted.")
        return department

    async def _get_user_if_valid(self, user_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[UserModel]:
        if not user_id:
            return None
        stmt = select(UserModel).where(UserModel.id == user_id, UserModel.organization_id == organization_id, UserModel.is_active == True)
        result = await self.db_session.execute(stmt)
        user = result.scalars().first()
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found in your organization or is inactive.")
        return user

    async def _get_valid_locations(self, location_ids: List[uuid.UUID], organization_id: uuid.UUID) -> List[LocationModel]:
        if not location_ids:
            return []
        stmt = select(LocationModel).where(
            LocationModel.id.in_(location_ids),
            LocationModel.organization_id == organization_id,
            LocationModel.is_deleted == False
        )
        result = await self.db_session.execute(stmt)
        locations = list(result.scalars().all())
        if len(locations) != len(set(location_ids)):
            # Identify missing or invalid IDs for a more specific error
            found_ids = {loc.id for loc in locations}
            missing_ids = set(location_ids) - found_ids
            raise NotFoundException(f"One or more locations not found or not in your organization: {missing_ids}")
        return locations

    async def _get_valid_applications(self, application_ids: List[uuid.UUID], organization_id: uuid.UUID) -> List[ApplicationModel]:
        if not application_ids:
            return []
        stmt = select(ApplicationModel).where(
            ApplicationModel.id.in_(application_ids),
            ApplicationModel.organization_id == organization_id,
            # Assuming ApplicationModel has an is_deleted or status field for active check
            # ApplicationModel.is_deleted == False # Or ApplicationModel.status == ApplicationStatusEnum.ACTIVE
        )
        # For now, let's assume applications don't have a soft delete status like others, or it's handled by status
        # If Application has a status like 'ARCHIVED' that means it's not usable, add that filter.
        result = await self.db_session.execute(stmt)
        applications = list(result.scalars().all())
        if len(applications) != len(set(application_ids)):
            found_ids = {app.id for app in applications}
            missing_ids = set(application_ids) - found_ids
            raise NotFoundException(f"One or more applications not found or not in your organization: {missing_ids}")
        return applications

    async def _get_valid_processes(self, process_ids: List[uuid.UUID], organization_id: uuid.UUID, current_process_id: Optional[uuid.UUID] = None) -> List[ProcessModel]:
        if not process_ids:
            return []
        # Ensure dependent processes belong to the same organization
        # current_process_id is used to prevent self-dependency if needed, though M2M handles this implicitly for direct self-loop
        query_ids = [pid for pid in process_ids if pid != current_process_id] if current_process_id else process_ids
        if not query_ids:
            return []
            
        stmt = (
            select(ProcessModel)
            .join(ProcessModel.department)
            .where(
                ProcessModel.id.in_(query_ids),
                DepartmentModel.organization_id == organization_id,
                ProcessModel.is_deleted == False
            )
        )
        result = await self.db_session.execute(stmt)
        processes = list(result.scalars().all())
        if len(processes) != len(set(query_ids)):
            found_ids = {p.id for p in processes}
            missing_ids = set(query_ids) - found_ids
            raise NotFoundException(f"One or more dependent processes not found or not in your organization: {missing_ids}")
        return processes

    async def create_process(self, process_data: ProcessCreate, current_user_id: uuid.UUID, organization_id: uuid.UUID) -> ProcessModel:
        # 1. Validate Department
        department = await self._get_department_if_valid(process_data.department_id, organization_id)

        # 2. Validate Process Owner (if provided)
        process_owner = None
        if process_data.process_owner_id:
            process_owner = await self._get_user_if_valid(process_data.process_owner_id, organization_id)

        # Check for duplicate name within the same department and organization
        name_check_stmt = select(ProcessModel).where(
            ProcessModel.name == process_data.name,
            ProcessModel.department_id == department.id, # Use validated department's ID
            ProcessModel.is_deleted == False
        )
        existing_process_with_name = await self.db_session.execute(name_check_stmt)
        if existing_process_with_name.scalars().first():
            raise ConflictException(f"A process with the name '{process_data.name}' already exists in the department '{department.name}'.")

        # Validate process locations as a subset of department locations
        process_locations_objects = []
        if process_data.location_ids:
            process_locations_objects = await self._get_valid_locations(process_data.location_ids, organization_id)
            department_location_ids = {loc.id for loc in department.locations} # department.locations loaded by _get_department_if_valid
            process_location_ids_to_check = {loc.id for loc in process_locations_objects}
            if not process_location_ids_to_check.issubset(department_location_ids):
                raise BadRequestException(
                    "One or more process locations are not associated with the selected department."
                )

        # 4. Create Process instance
        db_process = ProcessModel(
            name=process_data.name,
            description=process_data.description,
            department_id=department.id, # Assign validated department's ID
            process_owner_id=process_owner.id if process_owner else None,
            created_by_id=current_user_id,
            updated_by_id=current_user_id, # Initially, created_by and updated_by are the same
            rto=process_data.rto,
            rpo=process_data.rpo,
            criticality_level=process_data.criticality_level
        )

        # 5. Handle M2M relationships
        if process_data.location_ids:
            db_process.locations = process_locations_objects
        
        if process_data.application_ids:
            db_process.applications_used = await self._get_valid_applications(process_data.application_ids, organization_id)

        if process_data.upstream_dependency_ids:
            # For a new process, its ID isn't available yet for current_process_id exclusion, but it won't be in the list anyway.
            db_process.upstream_dependencies = await self._get_valid_processes(process_data.upstream_dependency_ids, organization_id)

        if process_data.downstream_dependency_ids:
            db_process.downstream_dependencies = await self._get_valid_processes(process_data.downstream_dependency_ids, organization_id)

        process_id_after_creation: Optional[uuid.UUID] = None
        try:
            self.db_session.add(db_process)
            await self.db_session.flush()  # Flush to get db_process.id if it's a default
            process_id_after_creation = db_process.id  # Capture the ID
            await self.db_session.commit()
        except IntegrityError as e:
            await self.db_session.rollback()
            # Check if it's the unique constraint for name and department
            if "_process_name_department_uc" in str(e).lower():
                 raise ConflictException(f"A process with the name '{process_data.name}' already exists in the department '{department.name}'.")
            # logger.error(f"Database integrity error creating process: {e}", exc_info=True)
            raise DatabaseException(f"Database error during process creation: {str(e)}")
        except Exception as e:
            await self.db_session.rollback()
            # logger.error(f"Unexpected error creating process: {e}", exc_info=True)
            raise DatabaseException(f"An unexpected error occurred while saving the process: {str(e)}")

        if not process_id_after_creation:
            # This should ideally not happen if flush/commit succeeded without error
            raise DatabaseException("Failed to retrieve process ID after creation.")

        # Re-fetch the process with all relationships needed for the response model
        stmt = (
            select(ProcessModel)
            .where(ProcessModel.id == process_id_after_creation)
            .options(
                selectinload(ProcessModel.department),
                selectinload(ProcessModel.process_owner),
                selectinload(ProcessModel.locations),
                selectinload(ProcessModel.applications_used),
                selectinload(ProcessModel.upstream_dependencies),
                selectinload(ProcessModel.downstream_dependencies),
                selectinload(ProcessModel.created_by),
                selectinload(ProcessModel.updated_by)
            )
        )
        result = await self.db_session.execute(stmt)
        created_process_loaded = result.scalars().one_or_none()

        if not created_process_loaded:
            raise NotFoundException(f"Failed to retrieve newly created process with ID {process_id_after_creation} after commit.")

        return created_process_loaded

    async def get_process_by_id(self, process_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[ProcessModel]:
        stmt = (
            select(ProcessModel)
            .join(ProcessModel.department).options(selectinload(DepartmentModel.locations))
            .where(
                ProcessModel.id == process_id,
                DepartmentModel.organization_id == organization_id,
                ProcessModel.is_deleted == False
            )
            .options(
                selectinload(ProcessModel.process_owner),
                selectinload(ProcessModel.locations),
                selectinload(ProcessModel.applications_used),
                selectinload(ProcessModel.upstream_dependencies),
                selectinload(ProcessModel.downstream_dependencies),
                selectinload(ProcessModel.created_by),
                selectinload(ProcessModel.updated_by)
            )
        )
        result = await self.db_session.execute(stmt)
        process = result.scalars().first()
        if not process:
            raise NotFoundException(f"Process with ID {process_id} not found or not in your organization.")
        return process

    async def get_all_processes(self, organization_id: uuid.UUID, skip: int = 0, limit: int = 100, sort_by: Optional[str] = None, sort_order: Optional[str] = "asc") -> Sequence[ProcessModel]:
        stmt = (
            select(ProcessModel)
            .join(ProcessModel.department)
            .where(
                DepartmentModel.organization_id == organization_id,
                ProcessModel.is_deleted == False
            )
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(ProcessModel.department),
                selectinload(ProcessModel.process_owner),
                selectinload(ProcessModel.locations),
                selectinload(ProcessModel.applications_used),
                selectinload(ProcessModel.upstream_dependencies),
                selectinload(ProcessModel.downstream_dependencies),
                selectinload(ProcessModel.created_by),
                selectinload(ProcessModel.updated_by)
            )
        )

        if sort_by:
            sort_column = getattr(ProcessModel, sort_by, None)
            if sort_column is None:
                # Potentially raise an error or log a warning for invalid sort_by column
                # For now, default to sorting by id or name if sort_by is invalid
                sort_column = ProcessModel.name 
            
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(sort_column.desc())
            else:
                stmt = stmt.order_by(sort_column.asc())
        else:
            # Default sort order if none specified
            stmt = stmt.order_by(ProcessModel.name.asc())

        result = await self.db_session.execute(stmt)
        processes = result.scalars().all()
        return processes

    async def count_processes(self, organization_id: uuid.UUID) -> int:
        stmt = (
            select(func.count(ProcessModel.id))
            .join(ProcessModel.department)
            .where(
                DepartmentModel.organization_id == organization_id,
                ProcessModel.is_deleted == False
            )
        )
        result = await self.db_session.execute(stmt)
        count = result.scalar_one_or_none() or 0
        return count

    async def update_process(self, process_id: uuid.UUID, process_data: ProcessUpdate, current_user_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[ProcessModel]:
        db_process = await self.get_process_by_id(process_id, organization_id)
        # get_process_by_id now loads db_process.department.locations
        if not db_process:
            raise NotFoundException(f"Process with ID {process_id} not found.")
        if db_process.is_deleted:
            raise UnprocessableEntityException(f"Process with ID {process_id} has been deleted and cannot be updated.")

        update_payload = process_data.model_dump(exclude_unset=True)
        updated_fields = False

        # Determine prospective department and its locations for validation
        prospective_department = db_process.department # Department if not changed
        if "department_id" in update_payload and update_payload["department_id"] != db_process.department_id:
            if update_payload["department_id"] is None:
                 raise BadRequestException("Department ID cannot be null.")
            prospective_department = await self._get_department_if_valid(update_payload["department_id"], organization_id)
            # prospective_department.locations are loaded by _get_department_if_valid

        # Determine prospective process locations for validation
        prospective_process_locations_objects = db_process.locations # Process locations if not changed
        if "location_ids" in update_payload:
            if update_payload["location_ids"]:
                prospective_process_locations_objects = await self._get_valid_locations(update_payload["location_ids"], organization_id)
            else: # Empty list means clear locations
                prospective_process_locations_objects = []
        
        # Validate process locations as a subset of department locations
        if prospective_process_locations_objects: # Only validate if process locations are intended to be non-empty
            # prospective_department.locations are already loaded
            department_location_ids_for_check = {loc.id for loc in prospective_department.locations}
            process_location_ids_for_check = {loc.id for loc in prospective_process_locations_objects}

            if not process_location_ids_for_check.issubset(department_location_ids_for_check):
                raise BadRequestException(
                    "One or more process locations are not associated with the (new or existing) department."
                )

        # Validate and update process owner if changed (can happen independently of location/department validation)
        new_process_owner = db_process.process_owner
        if "process_owner_id" in update_payload and update_payload["process_owner_id"] != (db_process.process_owner_id if db_process.process_owner else None):
            new_process_owner = await self._get_user_if_valid(update_payload["process_owner_id"], organization_id)
            updated_fields = True # Mark for commit even if only owner changes

        # Check for duplicate name if name or department is changing
        # Use prospective_department for the check if department is changing
        if "name" in update_payload or ("department_id" in update_payload and update_payload["department_id"] != db_process.department_id):
            check_name = update_payload.get("name", db_process.name)
            # Use prospective_department.id for the name check context
            check_department_id_for_name_check = prospective_department.id
            
            # Only perform DB check if the name or department context actually changes relative to current db_process state
            if check_name != db_process.name or check_department_id_for_name_check != db_process.department_id:
                name_check_stmt = select(ProcessModel).where(
                    ProcessModel.name == check_name,
                    ProcessModel.department_id == check_department_id_for_name_check,
                    ProcessModel.organization_id == organization_id,
                    ProcessModel.id != process_id,  # Exclude the current process
                    ProcessModel.is_deleted == False
                )
                existing_process_with_name = await self.db_session.execute(name_check_stmt)
                if existing_process_with_name.scalars().first():
                    raise ConflictException(f"A process with the name '{check_name}' already exists in the department '{prospective_department.name}'.")

        # Scalar field updates
        if "name" in update_payload and update_payload["name"] != db_process.name:
            db_process.name = update_payload["name"]
            updated_fields = True
        if "description" in update_payload and update_payload["description"] != db_process.description:
            db_process.description = update_payload["description"]
            updated_fields = True
        
        # Assign validated department (if it was changed)
        if prospective_department != db_process.department:
            db_process.department = prospective_department
            updated_fields = True
        
        # Assign validated process owner (if it was changed)
        # This check needs to be careful if new_process_owner is None and old was None
        if ("process_owner_id" in update_payload and 
            update_payload["process_owner_id"] != (db_process.process_owner_id if db_process.process_owner else None)):
            db_process.process_owner = new_process_owner
            db_process.process_owner_id = new_process_owner.id if new_process_owner else None
            updated_fields = True # Already marked if process_owner_id was in update_payload

        # Handle M2M relationships: Locations (assign prospective, already validated)
        if "location_ids" in update_payload:
            db_process.locations = prospective_process_locations_objects
            updated_fields = True

        # Handle M2M relationships: Upstream Dependencies
        if "upstream_dependency_ids" in update_payload:
            if update_payload["upstream_dependency_ids"]:
                # Prevent self-dependency by passing current process ID
                db_process.upstream_dependencies = await self._get_valid_processes(update_payload["upstream_dependency_ids"], organization_id, current_process_id=db_process.id)
                db_process.upstream_dependencies = await self._get_valid_processes(update_data["upstream_dependency_ids"], organization_id, current_process_id=db_process.id)
            else:
                db_process.upstream_dependencies = []
            updated_fields = True

        # Handle M2M relationships: Downstream Dependencies
        if "downstream_dependency_ids" in update_data:
            if update_data["downstream_dependency_ids"]:
                db_process.downstream_dependencies = await self._get_valid_processes(update_data["downstream_dependency_ids"], organization_id, current_process_id=db_process.id)
            else:
                db_process.downstream_dependencies = []
            updated_fields = True

        if updated_fields:
            db_process.updated_by_id = current_user_id
            # db_process.updated_at will be handled by SQLAlchemy's onupdate
            try:
                await self.db_session.commit()
                await self.db_session.refresh(db_process)
                # Eager load all relationships that might be in the response
                await self.db_session.refresh(db_process, attribute_names=[
                    'department', 'process_owner', 'locations', 'applications_used',
                    'upstream_dependencies', 'downstream_dependencies', 'created_by', 'updated_by'
                ])
            except Exception as e:
                await self.db_session.rollback()
                # Consider logging the exception e
                raise DatabaseException(f"Error updating process: {str(e)}")
        
        return db_process

    async def delete_process(self, process_id: uuid.UUID, current_user_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[ProcessModel]:
        db_process = await self.get_process_by_id(process_id, organization_id)
        if not db_process:
            # Should be caught by get_process_by_id, but defensive check
            raise NotFoundException(f"Process with ID {process_id} not found.")

        if db_process.is_deleted:
            # Optionally, could raise an error or just return the already deleted process
            # For now, let's treat it as idempotent if already deleted by returning it
            return db_process

        db_process.is_deleted = True
        db_process.deleted_at = datetime.utcnow() # Ensure datetime.utcnow() is imported or use func.now()
        db_process.updated_by_id = current_user_id
        # db_process.updated_at will be handled by SQLAlchemy's onupdate

        try:
            await self.db_session.commit()
            await self.db_session.refresh(db_process)
            # Eager load relationships for the response, even if deleted
            await self.db_session.refresh(db_process, attribute_names=[
                'department', 'process_owner', 'locations', 'applications_used',
                'upstream_dependencies', 'downstream_dependencies', 'created_by', 'updated_by'
            ])
        except Exception as e:
            await self.db_session.rollback()
            # Consider logging the exception e
            raise DatabaseException(f"Error deleting process: {str(e)}")

        return db_process

    # Helper methods for handling M2M relationships can be added here
    # e.g., _update_locations, _update_applications, _update_dependencies
