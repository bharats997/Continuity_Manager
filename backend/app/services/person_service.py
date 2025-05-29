# backend/app/services/person_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.domain.people import Person as PersonDB
from ..models.domain.roles import Role as RoleDB
from ..models.person import PersonCreate, PersonUpdate
from ..services.department_service import department_service # For validating departmentId
from ..services.location_service import location_service # For validating locationId

class PersonService:
    def get_person_by_id(
        self, db: Session, *, person_id: int, organization_id: int
    ) -> Optional[PersonDB]:
        return db.query(PersonDB).filter(
            PersonDB.id == person_id,
            PersonDB.organizationId == organization_id
        ).first()

    def get_person_by_email(
        self, db: Session, *, email: str, organization_id: int
    ) -> Optional[PersonDB]:
        return db.query(PersonDB).filter(
            PersonDB.email == email,
            PersonDB.organizationId == organization_id
        ).first()

    def get_people(
        self, db: Session, *, organization_id: int, skip: int = 0, limit: int = 100,
        is_active: Optional[bool] = True # Default to fetching active people
    ) -> List[PersonDB]:
        query = db.query(PersonDB).filter(PersonDB.organizationId == organization_id)
        if is_active is not None:
            query = query.filter(PersonDB.isActive == is_active)
        return query.order_by(PersonDB.lastName, PersonDB.firstName).offset(skip).limit(limit).all()

    def create_person(
        self, db: Session, *, person_in: PersonCreate, organization_id: int, current_user_id: int
    ) -> PersonDB:
        # Check for email uniqueness within the organization
        existing_person = self.get_person_by_email(db, email=person_in.email, organization_id=organization_id)
        if existing_person:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A person with this email already exists in this organization.",
            )

        # Validate departmentId if provided
        if person_in.departmentId:
            department = department_service.get_department_by_id(
                db, department_id=person_in.departmentId, organization_id=organization_id
            )
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Department with ID {person_in.departmentId} not found in this organization.",
                )
        
        # Validate locationId if provided
        if person_in.locationId:
            location = location_service.get_location_by_id_and_org(
                db, location_id=person_in.locationId, organization_id=organization_id
            )
            if not location:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Location with ID {person_in.locationId} not found in organization {organization_id}."
                )


        db_person = PersonDB(
            **person_in.model_dump(exclude={"roleIds"}),
            organizationId=organization_id,
            createdBy=current_user_id,
            updatedBy=current_user_id
        )

        # Validate and assign roles
        if person_in.roleIds:
            roles = db.query(RoleDB).filter(RoleDB.id.in_(person_in.roleIds)).all()
            if len(roles) != len(set(person_in.roleIds)): # Check if all provided role IDs were valid
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more role IDs are invalid.",
                )
            db_person.roles = roles
        
        db.add(db_person)
        db.commit()
        db.refresh(db_person)
        return db_person

    def update_person(
        self, db: Session, *, person_db: PersonDB, person_in: PersonUpdate, current_user_id: int
    ) -> PersonDB:
        update_data = person_in.model_dump(exclude_unset=True)

        if "email" in update_data and update_data["email"] != person_db.email:
            existing_person = self.get_person_by_email(db, email=update_data["email"], organization_id=person_db.organizationId)
            if existing_person and existing_person.id != person_db.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A person with this email already exists in this organization.",
                )
        
        if "departmentId" in update_data and update_data["departmentId"] is not None:
            department = department_service.get_department_by_id(
                db, department_id=update_data["departmentId"], organization_id=person_db.organizationId
            )
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Department with ID {update_data['departmentId']} not found in this organization.",
                )
        
        # Validate locationId if provided and changed
        if "locationId" in update_data and update_data["locationId"] is not None:
            location = location_service.get_location_by_id_and_org(
                db, location_id=update_data["locationId"], organization_id=person_db.organizationId
            )
            if not location:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Location with ID {update_data['locationId']} not found in organization {person_db.organizationId}."
                )

        for field, value in update_data.items():
            if field != "roleIds":
                setattr(person_db, field, value)
        
        if "roleIds" in update_data and update_data["roleIds"] is not None:
            roles = db.query(RoleDB).filter(RoleDB.id.in_(update_data["roleIds"])).all()
            if len(roles) != len(set(update_data["roleIds"])):
                 raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more role IDs are invalid for update.",
                )
            person_db.roles = roles
        
        person_db.updatedBy = current_user_id
        db.add(person_db)
        db.commit()
        db.refresh(person_db)
        return person_db

    def soft_delete_person(self, db: Session, *, person_db: PersonDB, current_user_id: int) -> PersonDB:
        if not person_db.isActive:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Person is already inactive.",
            )
        person_db.isActive = False
        person_db.updatedBy = current_user_id
        db.add(person_db)
        db.commit()
        db.refresh(person_db)
        return person_db

person_service = PersonService()
