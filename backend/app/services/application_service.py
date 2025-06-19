# backend/app/services/application_service.py
import uuid
from typing import List, Optional
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from ..schemas.applications import ApplicationRead # DEBUG IMPORT
from ..models.domain.applications import Application, ApplicationStatusEnum # ApplicationType is not directly used here but available via Application model
from ..models.domain.users import User
from ..models.domain.organizations import Organization
from ..models.domain.roles import Role # Added import for Role model
from ..schemas.applications import ApplicationCreate, ApplicationUpdate

class ApplicationService:
    async def get_application_by_id(
        self,
        db: AsyncSession,
        *,
        application_id: uuid.UUID,
        organization_id: uuid.UUID,
        status_filter: Optional[ApplicationStatusEnum] = ApplicationStatusEnum.ACTIVE
    ) -> Optional[Application]:
        """Retrieve a single application by its ID and organization ID, optionally filtering by status."""
        stmt = select(Application).options(
            selectinload(Application.organization),
            selectinload(Application.app_owner).options(
                selectinload(User.organization),
                selectinload(User.roles).selectinload(Role.permissions)
            ),
            selectinload(Application.created_by).options(
                selectinload(User.organization),
                selectinload(User.roles).selectinload(Role.permissions)
            ),
            selectinload(Application.updated_by).options(
                selectinload(User.organization),
                selectinload(User.roles).selectinload(Role.permissions)
            ),
        ).where(
            Application.id == application_id,
            Application.organization_id == organization_id
        )

        if status_filter is not None:
            stmt = stmt.where(Application.status == status_filter)

        result = await db.execute(stmt)
        application = result.scalar_one_or_none()

        return application

    # Removed the debug print from get_application_by_id_internal as it's moved to delete_application
    async def get_applications(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        name: Optional[str] = None,
        application_type: Optional[str] = None  # This is the string value e.g. "Owned"
    ) -> List[Application]:
        """Retrieve a list of active applications for an organization."""
        print(f"DEBUG SERVICE (get_applications): Received filters: name='{name}', application_type='{application_type}', org_id='{organization_id}', skip='{skip}', limit='{limit}'")
        stmt = (
            select(Application)
            .options(
                selectinload(Application.organization),
                selectinload(Application.app_owner).selectinload(User.roles).selectinload(Role.permissions),
                selectinload(Application.created_by).selectinload(User.roles).selectinload(Role.permissions),
                selectinload(Application.updated_by).selectinload(User.roles).selectinload(Role.permissions),
            )
            .where(Application.organization_id == organization_id, Application.status == ApplicationStatusEnum.ACTIVE)
        ) # Close the initial stmt definition here

        if name:
            stmt = stmt.where(Application.name.ilike(f"%{name}%"))
        
        if application_type:
            print(f"DEBUG SERVICE (get_applications): Applying type filter for application_type='{application_type}'")
            # Assuming application_type is a string like "Owned", "SAAS"
            # This requires Application.type to be a string field or ApplicationType enum to be handled correctly.
            # If Application.type is an Enum, direct comparison might be needed, e.g. Application.type == ApplicationType[application_type.upper()]
            # For now, assuming it's a string field that can be directly compared or the enum's value.
            # Let's assume Application.type stores the string value of the enum (e.g., 'Owned', 'SAAS')
            stmt = stmt.where(Application.type == application_type)

        stmt = (
            stmt.order_by(Application.name)
            .offset(skip)
            .limit(limit)
        )
        # from sqlalchemy.dialects import sqlite
        # print(f"DEBUG SERVICE (get_applications): SQL Query: {stmt.compile(dialect=sqlite.dialect(), compile_kwargs={'literal_binds': True})}")
        result = await db.execute(stmt)
        applications = result.scalars().all()
        
        # Explicitly refresh each application to ensure all relationships are loaded before Pydantic serialization.
        # This is a workaround for potential issues where selectinload might not behave as expected in all async scenarios.
        for app in applications:
            await db.refresh(app, attribute_names=["organization", "app_owner", "created_by", "updated_by"])
            
        print(f"DEBUG SERVICE (get_applications): Found {len(applications)} applications matching criteria.")
        return applications

    async def create_application(
        self, db: AsyncSession, *, application_in: ApplicationCreate, current_user: User
    ) -> Application:
        """Create a new application. current_user is passed for context if needed but PRD implies Admin can specify org_id."""
        
        # Validate organization_id from input
        org_stmt = select(Organization).where(Organization.id == application_in.organization_id)
        organization = (await db.execute(org_stmt)).scalar_one_or_none()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization with id {application_in.organization_id} not found.",
            )

        # Check for unique application name within the organization
        name_check_stmt = select(Application).where(
            Application.name == application_in.name,
            Application.organization_id == application_in.organization_id,
            Application.status == ApplicationStatusEnum.ACTIVE # Corrected: Use status enum
        )
        existing_application = (await db.execute(name_check_stmt)).scalar_one_or_none()
        if existing_application:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Application with name '{application_in.name}' already exists in this organization.",
            )

        # Validate app_owner_id if provided
        if application_in.app_owner_id:
            owner_stmt = select(User).where(
                User.id == application_in.app_owner_id,
                User.organization_id == application_in.organization_id # Ensure owner is in the same org
            )
            app_owner = (await db.execute(owner_stmt)).scalar_one_or_none()
            if not app_owner:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"App owner with id {application_in.app_owner_id} not found in organization {application_in.organization_id}.",
                )
        
        # Create Application instance directly from the Pydantic model to avoid mapping issues
        db_application = Application(
            name=application_in.name,
            description=application_in.description,
            type=application_in.type, # type is passed as a string value from the test
            organization_id=application_in.organization_id,
            app_owner_id=application_in.app_owner_id,
            status=application_in.status.value if application_in.status else None,  # status is an enum object
            version=application_in.version,
            vendor=application_in.vendor,
            criticality=application_in.criticality,
            hosted_on=application_in.hosted_on,
            workarounds=application_in.workarounds,
            derived_rto=application_in.derived_rto,
            created_by_id=current_user.id,
            updated_by_id=current_user.id
        )

        db.add(db_application)
        try:
            await db.commit()
            # Instead of re-fetching, refresh the instance we just created to load relationships.
            # This is a more direct way to ensure the object is ready for serialization.
            await db.refresh(db_application, attribute_names=["organization", "app_owner", "created_by", "updated_by"])
            return db_application
        except IntegrityError as e:
            await db.rollback()
            # Consider logging the full error e for debugging
            # logger.error(f"Integrity error creating application: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database integrity error while creating application. Possible duplicate name or invalid foreign key.",
            )
        except Exception as e:
            await db.rollback()
            # Consider logging the full error e for debugging
            # logger.error(f"Unexpected error creating application: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred while creating the application: {str(e)}",
            )
        return db_application

    async def update_application(
        self,
        db: AsyncSession,
        *,
        application_id: uuid.UUID,
        application_in: ApplicationUpdate,
        organization_id: uuid.UUID, # Used to scope the query for the application to update
    ) -> Optional[Application]:
        """Update an existing application, ensuring it belongs to the specified organization."""
        # Fetch the existing application scoped by organization_id, regardless of its current status
        db_application = await self.get_application_by_id(
            db, application_id=application_id, organization_id=organization_id, status_filter=None
        )
        if not db_application:
            return None 

        update_data = application_in.model_dump(exclude_unset=True)

        # If name is being updated, check for uniqueness within the organization
        if "name" in update_data and update_data["name"] != db_application.name:
            name_check_stmt = select(Application).where(
                Application.name == update_data["name"],
                Application.organization_id == organization_id,
                Application.id != application_id, # Exclude the current application
                Application.status == ApplicationStatusEnum.ACTIVE
            )
            existing_application = (await db.execute(name_check_stmt)).scalar_one_or_none()
            if existing_application:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Application with name '{update_data['name']}' already exists in this organization.",
                )
        
        # Validate app_owner_id if provided and changed
        if "app_owner_id" in update_data and update_data["app_owner_id"] is not None:
            # Only validate if the app_owner_id is actually changing to a new value
            if update_data["app_owner_id"] != db_application.app_owner_id:
                owner_stmt = select(User).where(
                    User.id == update_data["app_owner_id"],
                    User.organization_id == organization_id # Ensure owner is in the same org
                )
                app_owner = (await db.execute(owner_stmt)).scalar_one_or_none()
                if not app_owner:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"App owner with id {update_data['app_owner_id']} not found in organization {organization_id}.",
                    )
        elif "app_owner_id" in update_data and update_data["app_owner_id"] is None:
            # If app_owner_id is explicitly set to None, allow it (if model allows nullable)
            pass # setattr will handle this
        
        # organization_id cannot be changed via this update method
        if "organization_id" in update_data:
            del update_data["organization_id"]

        for field, value in update_data.items():
            if field == "app_owner_id":
                print(f"DEBUG SERVICE (update_application): Attempting to set app_owner_id to: {value} (type: {type(value)}) on instance {id(db_application)}")
            setattr(db_application, field, value)
        
        db.add(db_application)
        try:
            await db.commit()
            # Instead of re-fetching, refresh the instance we just updated to load relationships.
            await db.refresh(db_application, attribute_names=["organization", "app_owner", "created_by", "updated_by"])
            return db_application
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database integrity error: {e.orig}",
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}",
            )
        return db_application

    async def delete_application(
        self, db: AsyncSession, *, application_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Optional[Application]:
        """Soft delete an application by setting its status to INACTIVE, ensuring it belongs to the specified organization."""
        db_application = await self.get_application_by_id(
            db, application_id=application_id, organization_id=organization_id
        )
        
        if not db_application:
            return None 

        db_application.status = ApplicationStatusEnum.INACTIVE
        db_application.is_active = False # Explicitly set is_active to False
    
        db.add(db_application)
        try:
            await db.commit()
            # Instead of re-fetching, refresh the instance we just updated to load relationships.
            await db.refresh(db_application, attribute_names=["organization", "app_owner", "created_by", "updated_by"])
            return db_application
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred during soft deletion: {str(e)}",
            )
        return db_application

application_service = ApplicationService()
