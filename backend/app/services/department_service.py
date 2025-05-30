# backend/app/services/department_service.py
from typing import List, Optional
from datetime import datetime # Added for soft delete timestamp
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from ..models.domain.departments import Department as DepartmentModel # SQLAlchemy model
from ..models.domain.locations import Location as LocationModel # SQLAlchemy model
from ..models.department import DepartmentCreate, DepartmentUpdate # Pydantic models

class DepartmentService:
    def get_department_by_id(self, db: Session, department_id: int, organization_id: Optional[int] = None) -> Optional[DepartmentModel]:
        query = db.query(DepartmentModel).filter(DepartmentModel.id == department_id, DepartmentModel.is_deleted == False)
        if organization_id:
            query = query.filter(DepartmentModel.organizationId == organization_id)
        return query.options(
            joinedload(DepartmentModel.department_head),
            joinedload(DepartmentModel.locations)
        ).first()

    def get_all_departments(self, db: Session, skip: int = 0, limit: int = 100) -> List[DepartmentModel]:
        return db.query(DepartmentModel).filter(DepartmentModel.is_deleted == False).offset(skip).limit(limit).all()

    def get_departments_by_organization(self, db: Session, organization_id: int, skip: int = 0, limit: int = 100) -> List[DepartmentModel]:
        return db.query(DepartmentModel).filter(DepartmentModel.organizationId == organization_id, DepartmentModel.is_deleted == False).options(
            joinedload(DepartmentModel.department_head),
            joinedload(DepartmentModel.locations)
        ).offset(skip).limit(limit).all()

    def create_department(self, db: Session, department_in: DepartmentCreate) -> DepartmentModel:
        # Basic check, more complex validation could be here or in Pydantic model
        existing_department = db.query(DepartmentModel).filter(
            DepartmentModel.name == department_in.name,
            DepartmentModel.organizationId == department_in.organizationId,
            DepartmentModel.is_deleted == False
        ).first()
        if existing_department:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Department with this name already exists in the organization."
            )
        
        db_department = DepartmentModel(
            name=department_in.name,
            description=department_in.description,
            organizationId=department_in.organizationId,
            department_head_id=department_in.department_head_id,
            number_of_team_members=department_in.number_of_team_members
            # createdBy=current_user_id, # If tracking user
            # updatedBy=current_user_id  # If tracking user
        )
        if department_in.location_ids:
            locations = db.query(LocationModel).filter(
                LocationModel.id.in_(department_in.location_ids),
                LocationModel.organizationId == department_in.organizationId
            ).all()
            if len(locations) != len(set(department_in.location_ids)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more locations not found or do not belong to the specified organization."
                )
            db_department.locations = locations
        db.add(db_department)
        db.commit()
        db.refresh(db_department)
        return db_department

    def update_department(self, db: Session, department_id: int, department_in: DepartmentUpdate, organization_id: Optional[int] = None) -> Optional[DepartmentModel]:
        db_department = self.get_department_by_id(db, department_id=department_id, organization_id=organization_id)
        if not db_department:
            return None # Or raise HTTPException(status_code=404, detail="Department not found")

        update_data = department_in.model_dump(exclude_unset=True) # Pydantic V2 uses model_dump

        for field, value in update_data.items():
            if field not in ['location_ids']: # Handle location_ids separately
                setattr(db_department, field, value)

        if 'location_ids' in update_data:
            location_ids = update_data['location_ids']
            if location_ids is not None: # Allows clearing locations with an empty list
                if location_ids: # If list is not empty, fetch and assign
                    locations = db.query(LocationModel).filter(
                        LocationModel.id.in_(location_ids),
                        LocationModel.organizationId == db_department.organizationId
                    ).all()
                    if len(locations) != len(set(location_ids)):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="One or more locations not found or do not belong to the department's organization."
                        )
                    db_department.locations = locations
                else: # Empty list provided, clear existing locations
                    db_department.locations = []
        
        # db_department.updatedBy = current_user_id # If tracking user
        db.add(db_department)
        db.commit()
        db.refresh(db_department)
        return db_department

    def delete_department(self, db: Session, department_id: int, organization_id: Optional[int] = None) -> Optional[DepartmentModel]:
        # get_department_by_id already filters for is_deleted == False
        db_department = self.get_department_by_id(db, department_id=department_id, organization_id=organization_id)
        
        if not db_department:
            # If it's not found (and not soft-deleted), or if it was already soft-deleted, it won't be returned by get_department_by_id.
            # So, we can raise a 404 here as it's not available for deletion.
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found or already deleted")

        db_department.is_deleted = True
        db_department.deleted_at = datetime.utcnow() # Consider timezone if your DB expects it
        # db_department.isActive = False # Optionally, also set isActive to False
        
        db.add(db_department)
        db.commit()
        db.refresh(db_department)
        return db_department

# Create an instance of the service
department_service = DepartmentService()
