# backend/app/services/department_service.py
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.domain.departments import Department as DepartmentModel
from ..models.domain.locations import Location as LocationModel
from ..models.domain.organizations import Organization as OrganizationModel
from ..models.domain.users import User as UserModel
from ..schemas.department import DepartmentCreate, DepartmentUpdate


class DepartmentService:
    async def get_department_by_id(
        self,
        db: AsyncSession,
        department_id: uuid.UUID,
        organization_id: Optional[uuid.UUID] = None,
    ) -> Optional[DepartmentModel]:
        stmt = select(DepartmentModel).where(
            DepartmentModel.id == department_id, DepartmentModel.is_deleted == False
        )
        if organization_id:
            stmt = stmt.where(DepartmentModel.organizationId == organization_id)
        stmt = stmt.options(
            joinedload(DepartmentModel.department_head),
            joinedload(DepartmentModel.locations),
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_all_departments(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[DepartmentModel]:
        stmt = (
            select(DepartmentModel)
            .where(DepartmentModel.is_deleted == False)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_departments_by_organization(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DepartmentModel]:
        stmt = (
            select(DepartmentModel)
            .where(
                DepartmentModel.organizationId == organization_id,
                DepartmentModel.is_deleted == False,
            )
            .options(
                joinedload(DepartmentModel.department_head),
                joinedload(DepartmentModel.locations),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create_department(
        self, db: AsyncSession, department_in: DepartmentCreate, organization_id: uuid.UUID
    ) -> DepartmentModel:
        # Validate Organization ID existence
        org_stmt = select(OrganizationModel).where(
            OrganizationModel.id == organization_id, OrganizationModel.isActive == True
        )
        organization = (await db.execute(org_stmt)).scalars().first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Organization with ID {organization_id} not found or is deleted.",
            )

        # Validate Department Head ID if provided
        if department_in.department_head_id:
            head_stmt = select(UserModel).where(
                UserModel.id == department_in.department_head_id,
                UserModel.organizationId == organization_id,
                UserModel.is_active == True,
            )
            department_head = (await db.execute(head_stmt)).scalars().first()
            if not department_head:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Department head with ID {department_in.department_head_id} not found, inactive, deleted, or does not belong to organization {organization_id}.",
                )

        # Basic check for existing department name
        existing_dept_stmt = select(DepartmentModel).where(
            DepartmentModel.name == department_in.name,
            DepartmentModel.organizationId == organization_id,
            DepartmentModel.is_deleted == False,
        )
        existing_department = (await db.execute(existing_dept_stmt)).scalars().first()
        if existing_department:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Department with name '{department_in.name}' already exists in this organization.",
            )

        # Validate Location IDs if provided
        valid_locations = []
        if department_in.location_ids:
            loc_stmt = select(LocationModel).where(
                LocationModel.id.in_(department_in.location_ids),
                LocationModel.organizationId == organization_id,
                LocationModel.isActive == True,
            )
            fetched_locations = (await db.execute(loc_stmt)).scalars().all()
            if len(fetched_locations) != len(set(department_in.location_ids)):
                fetched_ids = {loc.id for loc in fetched_locations}
                problematic_ids = set(department_in.location_ids) - fetched_ids
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"One or more location IDs are invalid, not found in organization {organization_id}, or inactive: {problematic_ids}",
                )
            valid_locations = fetched_locations

        create_data = department_in.model_dump(exclude={"location_ids"})
        create_data["organizationId"] = organization_id
        db_department = DepartmentModel(**create_data, locations=valid_locations)

        db.add(db_department)
        await db.commit()
        await db.refresh(db_department)
        return db_department

    async def update_department(
        self,
        db: AsyncSession,
        department_id: uuid.UUID,
        department_in: DepartmentUpdate,
        organization_id: uuid.UUID,
    ) -> Optional[DepartmentModel]:
        db_department = await self.get_department_by_id(
            db, department_id=department_id, organization_id=organization_id
        )
        if not db_department:
            return None

        update_data = department_in.model_dump(exclude_unset=True)

        if "department_head_id" in update_data and update_data["department_head_id"] is not None:
            head_stmt = select(UserModel).where(
                UserModel.id == update_data["department_head_id"],
                UserModel.organizationId == organization_id,
                UserModel.is_active == True,
            )
            department_head_candidate = (await db.execute(head_stmt)).scalars().first()
            if not department_head_candidate:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Department head with ID {update_data['department_head_id']} not found in organization {organization_id}, is inactive, or does not exist.",
                )

        for field, value in update_data.items():
            if field not in ["location_ids"]:
                setattr(db_department, field, value)

        if "location_ids" in update_data:
            location_ids = update_data.get("location_ids")
            valid_locations = []
            if location_ids is not None:
                if location_ids:
                    loc_stmt = select(LocationModel).where(
                        LocationModel.id.in_(location_ids),
                        LocationModel.organizationId == organization_id,
                        LocationModel.isActive == True,
                    )
                    fetched_locations = (await db.execute(loc_stmt)).scalars().all()
                    if len(fetched_locations) != len(set(location_ids)):
                        fetched_ids = {loc.id for loc in fetched_locations}
                        problematic_ids = set(location_ids) - fetched_ids
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"One or more location IDs are invalid, not found in organization {organization_id}, or inactive: {problematic_ids}",
                        )
                    valid_locations = fetched_locations
                db_department.locations = valid_locations

        db.add(db_department)
        await db.commit()
        await db.refresh(db_department)
        return db_department

    async def delete_department(
        self, db: AsyncSession, department_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Optional[DepartmentModel]:
        db_department = await self.get_department_by_id(
            db, department_id=department_id, organization_id=organization_id
        )
        if not db_department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found or already deleted",
            )

        db_department.is_deleted = True
        db_department.deleted_at = datetime.utcnow()

        db.add(db_department)
        await db.commit()
        await db.refresh(db_department)
        return db_department


department_service = DepartmentService()
