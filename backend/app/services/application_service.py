# backend/app/services/application_service.py
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

from ..models.domain.applications import Application as ApplicationDomain
from ..models.domain.people import Person as PersonDomain # For creator/updater/deleter relationships
from ..models.domain.organizations import Organization as OrganizationDomain # For organization relationship
from ..models.application import ApplicationCreate, ApplicationUpdate

class ApplicationService:
    def get_application(self, db: Session, application_id: int) -> Optional[ApplicationDomain]:
        """Retrieve a single application by its ID, with related objects eagerly loaded."""
        return (
            db.query(ApplicationDomain)
            .options(
                joinedload(ApplicationDomain.organization),
                joinedload(ApplicationDomain.appOwner),
                joinedload(ApplicationDomain.creator),
                joinedload(ApplicationDomain.updater),
                joinedload(ApplicationDomain.deleter),
            )
            .filter(ApplicationDomain.id == application_id, ApplicationDomain.deletedAt.is_(None))
            .first()
        )

    def get_applications(
        self, db: Session, skip: int = 0, limit: int = 100, organization_id: Optional[int] = None
    ) -> List[ApplicationDomain]:
        """Retrieve a list of applications, with optional filtering by organization_id."""
        query = (
            db.query(ApplicationDomain)
            .options(
                joinedload(ApplicationDomain.organization),
                joinedload(ApplicationDomain.appOwner),
                # Eager load creator/updater if frequently accessed in lists, otherwise consider deferring
                # joinedload(ApplicationDomain.creator),
                # joinedload(ApplicationDomain.updater),
            )
            .filter(ApplicationDomain.deletedAt.is_(None))
        )
        if organization_id is not None:
            query = query.filter(ApplicationDomain.organizationId == organization_id)
        
        return query.order_by(ApplicationDomain.name).offset(skip).limit(limit).all()

    def create_application(
        self, db: Session, application_in: ApplicationCreate, creator_id: int
    ) -> ApplicationDomain:
        """Create a new application."""
        # Check if organization exists
        organization = db.query(OrganizationDomain).filter(OrganizationDomain.id == application_in.organizationId).first()
        if not organization:
            raise ValueError(f"Organization with id {application_in.organizationId} not found.")

        # Check if app owner exists, if provided
        if application_in.appOwnerId:
            app_owner = db.query(PersonDomain).filter(PersonDomain.id == application_in.appOwnerId).first()
            if not app_owner:
                raise ValueError(f"App owner with id {application_in.appOwnerId} not found.")

        db_application = ApplicationDomain(
            **application_in.model_dump(),
            createdBy=creator_id,
            updatedBy=creator_id # Also set updatedBy on creation
        )
        db.add(db_application)
        try:
            db.commit()
            db.refresh(db_application)
            # Eagerly load relationships for the returned object
            return self.get_application(db, db_application.id)
        except IntegrityError as e:
            db.rollback()
            # You might want to check for specific integrity errors, e.g., unique constraints
            raise ValueError(f"Error creating application: {e.orig}")
        except Exception as e:
            db.rollback()
            raise e

    def update_application(
        self, db: Session, application_id: int, application_in: ApplicationUpdate, updater_id: int
    ) -> Optional[ApplicationDomain]:
        """Update an existing application."""
        db_application = self.get_application(db, application_id)
        if not db_application:
            return None

        update_data = application_in.model_dump(exclude_unset=True)

        # Validate appOwnerId if provided
        if 'appOwnerId' in update_data and update_data['appOwnerId'] is not None:
            app_owner = db.query(PersonDomain).filter(PersonDomain.id == update_data['appOwnerId']).first()
            if not app_owner:
                raise ValueError(f"App owner with id {update_data['appOwnerId']} not found.")
        
        # Typically, organizationId is not updatable for an application via this method.
        # If it were, similar validation for organizationId would be needed.
        # if 'organizationId' in update_data:
        #     del update_data['organizationId'] # Or handle as a special case

        for field, value in update_data.items():
            setattr(db_application, field, value)
        
        db_application.updatedAt = datetime.utcnow() # Consider timezone if your DB stores UTC
        db_application.updatedBy = updater_id
        
        db.add(db_application)
        try:
            db.commit()
            db.refresh(db_application)
            # Eagerly load relationships for the returned object
            return self.get_application(db, db_application.id)
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Error updating application: {e.orig}")
        except Exception as e:
            db.rollback()
            raise e

    def delete_application(
        self, db: Session, application_id: int, deleter_id: int
    ) -> Optional[ApplicationDomain]:
        """Soft delete an application by setting the deletedAt timestamp."""
        db_application = self.get_application(db, application_id)
        if not db_application:
            return None
        
        if db_application.deletedAt is not None:
            # Already soft-deleted, or handle as an error/idempotent case
            return db_application # Or raise an error: raise ValueError("Application already deleted.")

        db_application.deletedAt = datetime.now(timezone.utc) # Ensure timezone-aware
        db_application.deletedBy = deleter_id
        db_application.isActive = False # Also mark as inactive
        
        db.add(db_application)
        try:
            db.commit()
            db.refresh(db_application)
            # To ensure relationships are loaded as expected by the response model,
            # we might need to explicitly load them here if they are not already loaded
            # or if the refresh doesn't cover them sufficiently for the serializer.
            # For now, let's return the refreshed object.
            # If specific relationships are missing in the response, we can address that.
            return db_application
        except Exception as e:
            db.rollback()
            raise e

application_service = ApplicationService()
