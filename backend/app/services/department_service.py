# backend/app/services/department_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.domain.departments import Department as DepartmentModel # SQLAlchemy model
from ..models.department import DepartmentCreate, DepartmentUpdate # Pydantic models

class DepartmentService:
    def get_department_by_id(self, db: Session, department_id: int, organization_id: Optional[int] = None) -> Optional[DepartmentModel]:
        query = db.query(DepartmentModel).filter(DepartmentModel.id == department_id)
        if organization_id:
            query = query.filter(DepartmentModel.organizationId == organization_id)
        return query.first()

    def get_all_departments(self, db: Session, skip: int = 0, limit: int = 100) -> List[DepartmentModel]:
        return db.query(DepartmentModel).offset(skip).limit(limit).all()

    def get_departments_by_organization(self, db: Session, organization_id: int, skip: int = 0, limit: int = 100) -> List[DepartmentModel]:
        return db.query(DepartmentModel).filter(DepartmentModel.organizationId == organization_id).offset(skip).limit(limit).all()

    def create_department(self, db: Session, department_in: DepartmentCreate) -> DepartmentModel:
        # Basic check, more complex validation could be here or in Pydantic model
        existing_department = db.query(DepartmentModel).filter(
            DepartmentModel.name == department_in.name,
            DepartmentModel.organizationId == department_in.organizationId
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
            # createdBy=current_user_id, # If tracking user
            # updatedBy=current_user_id  # If tracking user
        )
        db.add(db_department)
        db.commit()
        db.refresh(db_department)
        return db_department

    def update_department(self, db: Session, department_id: int, department_in: DepartmentUpdate, organization_id: Optional[int] = None) -> Optional[DepartmentModel]:
        db_department = self.get_department_by_id(db, department_id=department_id, organization_id=organization_id)
        if not db_department:
            return None # Or raise HTTPException(status_code=404, detail="Department not found")

        update_data = department_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_department, field, value)
        
        # db_department.updatedBy = current_user_id # If tracking user
        db.add(db_department)
        db.commit()
        db.refresh(db_department)
        return db_department

    def delete_department(self, db: Session, department_id: int, organization_id: Optional[int] = None) -> bool:
        db_department = self.get_department_by_id(db, department_id=department_id, organization_id=organization_id)
        if not db_department:
            # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
            return False
        
        db.delete(db_department)
        db.commit()
        return True

# Create an instance of the service
department_service = DepartmentService()
