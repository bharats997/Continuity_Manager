# backend/app/services/location_service.py
import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from ..models.domain.locations import Location
from ..schemas.location import LocationCreate, LocationUpdate
from ..models.domain.organizations import Organization as OrganizationModel

class LocationService:
    async def get_location_by_id_and_org(self, db: AsyncSession, location_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[Location]:
        """
        Retrieves a location by its ID, ensuring it belongs to the specified organization.
        """
        query = select(Location).filter(
            Location.id == location_id,
            Location.organizationId == organization_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_location(self, db: AsyncSession, location_id: uuid.UUID) -> Optional[Location]:
        """
        Retrieves a location by its ID.
        """
        query = select(Location).filter(Location.id == location_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_locations_for_organization(
        self, db: AsyncSession, organization_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Location]:
        """
        Retrieves all locations for a given organization.
        """
        org_query = select(OrganizationModel).filter(OrganizationModel.id == organization_id)
        organization = (await db.execute(org_query)).scalar_one_or_none()
        if not organization:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        
        query = (
            select(Location)
            .options(joinedload(Location.organization))
            .filter(Location.organizationId == organization_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def count_locations_for_organization(self, db: AsyncSession, organization_id: uuid.UUID) -> int:
        """
        Counts all locations for a given organization.
        """
        query = select(func.count()).select_from(Location).filter(Location.organizationId == organization_id)
        count = await db.execute(query)
        return count.scalar()

    async def create_location(self, db: AsyncSession, location_in: LocationCreate) -> Location:
        """
        Creates a new location. The organizationId is expected in location_in.
        """
        org_query = select(OrganizationModel).filter(OrganizationModel.id == location_in.organizationId)
        organization = (await db.execute(org_query)).scalar_one_or_none()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization with id {location_in.organizationId} not found."
            )

        existing_location_query = (
            select(Location)
            .filter(Location.name == location_in.name, Location.organizationId == location_in.organizationId)
        )
        existing_location = (await db.execute(existing_location_query)).scalar_one_or_none()
        if existing_location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Location with name '{location_in.name}' already exists in this organization."
            )

        db_location = Location(**location_in.model_dump())
        db.add(db_location)
        await db.commit()
        await db.refresh(db_location)
        return db_location

    async def update_location(
        self, db: AsyncSession, location_id: uuid.UUID, location_in: LocationUpdate
    ) -> Optional[Location]:
        """
        Updates an existing location.
        """
        db_location_query = select(Location).filter(Location.id == location_id)
        db_location = (await db.execute(db_location_query)).scalar_one_or_none()
        if not db_location:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

        update_data = location_in.model_dump(exclude_unset=True)
        
        if "name" in update_data and update_data["name"] != db_location.name:
            existing_location_query = (
                select(Location)
                .filter(
                    Location.name == update_data["name"], 
                    Location.organizationId == db_location.organizationId, 
                    Location.id != location_id
                )
            )
            existing_location = (await db.execute(existing_location_query)).scalar_one_or_none()
            if existing_location:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Another location with name '{update_data['name']}' already exists in this organization."
                )

        for key, value in update_data.items():
            setattr(db_location, key, value)

        db.add(db_location)
        await db.commit()
        await db.refresh(db_location)
        return db_location

    async def delete_location(self, db: AsyncSession, location_id: uuid.UUID) -> Optional[Location]:
        """
        Deletes a location.
        """
        db_location_query = select(Location).filter(Location.id == location_id)
        db_location = (await db.execute(db_location_query)).scalar_one_or_none()
        if not db_location:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
        
        await db.delete(db_location)
        await db.commit()
        return db_location

location_service = LocationService()
