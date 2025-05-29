# backend/app/services/location_service.py
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from ..models.domain.locations import Location
from ..models.location import LocationCreate, LocationUpdate
from ..models.domain.organizations import Organization as OrganizationModel

class LocationService:
    def get_location_by_id_and_org(self, db: Session, location_id: int, organization_id: int) -> Optional[Location]:
        """
        Retrieves a location by its ID, ensuring it belongs to the specified organization.
        """
        location = db.query(Location).filter(
            Location.id == location_id,
            Location.organizationId == organization_id
        ).first()
        # No explicit 404 here, service using this should handle if location is None
        # Or, if we want to enforce 404 from here:
        # if not location:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail=f"Location with ID {location_id} not found in organization {organization_id}."
        #     )
        return location

    def get_location(self, db: Session, location_id: int) -> Optional[Location]:
        """
        Retrieves a location by its ID.
        """
        location = db.query(Location).filter(Location.id == location_id).first()
        # Service methods using this should handle if location is None or raise 404
        # For example, the API layer calling this might raise HTTPException
        return location

    def get_all_locations_for_organization(
        self, db: Session, organization_id: int, skip: int = 0, limit: int = 100
    ) -> List[Location]:
        """
        Retrieves all locations for a given organization.
        """
        organization = db.query(OrganizationModel).filter(OrganizationModel.id == organization_id).first()
        if not organization:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        
        return (
            db.query(Location)
            .options(joinedload(Location.organization))
            .filter(Location.organizationId == organization_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_location(self, db: Session, location_in: LocationCreate) -> Location:
        """
        Creates a new location. The organizationId is expected in location_in.
        """
        organization = db.query(OrganizationModel).filter(OrganizationModel.id == location_in.organizationId).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization with id {location_in.organizationId} not found."
            )

        existing_location = (
            db.query(Location)
            .filter(Location.name == location_in.name, Location.organizationId == location_in.organizationId)
            .first()
        )
        if existing_location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Location with name '{location_in.name}' already exists in this organization."
            )

        db_location = Location(**location_in.model_dump())
        db.add(db_location)
        db.commit()
        db.refresh(db_location)
        return db_location

    def update_location(
        self, db: Session, location_id: int, location_in: LocationUpdate
    ) -> Optional[Location]:
        """
        Updates an existing location.
        """
        db_location = db.query(Location).filter(Location.id == location_id).first()
        if not db_location:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

        update_data = location_in.model_dump(exclude_unset=True)
        
        if "name" in update_data and update_data["name"] != db_location.name:
            existing_location = (
                db.query(Location)
                .filter(
                    Location.name == update_data["name"], 
                    Location.organizationId == db_location.organizationId, 
                    Location.id != location_id
                )
                .first()
            )
            if existing_location:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Another location with name '{update_data['name']}' already exists in this organization."
                )

        for key, value in update_data.items():
            setattr(db_location, key, value)

        db.add(db_location)
        db.commit()
        db.refresh(db_location)
        return db_location

    def delete_location(self, db: Session, location_id: int) -> Optional[Location]:
        """
        Deletes a location.
        """
        db_location = db.query(Location).filter(Location.id == location_id).first()
        if not db_location:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
        
        # Consider if we need to check organization_id before deleting, 
        # but typically delete operations are on a specific ID.
        db.delete(db_location)
        db.commit()
        return db_location

location_service = LocationService()
