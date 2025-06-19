import uuid
from typing import List, Optional, Sequence
from sqlalchemy import select, update as sqlalchemy_update, delete as sqlalchemy_delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models.domain.vendors import Vendor as VendorModel
from app.models.domain.users import User  # Added for nested selectinload of user roles
from app.models.domain.roles import Role  # Added for nested selectinload of role permissions
from app.schemas.vendors import VendorCreate, VendorUpdate
from app.services.base_service import BaseService
from app.utils.exceptions import NotFoundError, ConflictException, DatabaseException, UnprocessableEntityException

class VendorService(BaseService[VendorModel, VendorCreate, VendorUpdate]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(VendorModel, db_session)

    async def create_vendor(self, vendor_data: VendorCreate, current_user_id: uuid.UUID, organization_id: uuid.UUID) -> VendorModel:
        # Check for duplicate vendor name within the same organization
        name_check_stmt = select(VendorModel).where(
            VendorModel.name == vendor_data.name,
            VendorModel.organization_id == organization_id,
            VendorModel.is_active == True # Or check is_deleted == False if using that pattern
        )
        existing_vendor_with_name = await self.db_session.execute(name_check_stmt)
        if existing_vendor_with_name.scalars().first():
            raise ConflictException(f"A vendor with the name '{vendor_data.name}' already exists in your organization.")

        db_vendor = VendorModel(
            **vendor_data.model_dump(),
            organization_id=organization_id,
            created_by_id=current_user_id,
            updated_by_id=current_user_id
        )
        self.db_session.add(db_vendor)
        try:
            await self.db_session.commit()
            await self.db_session.refresh(db_vendor)
            # Ensure all relevant relationships are loaded after creation
            await self.db_session.refresh(db_vendor, attribute_names=['organization', 'created_by', 'updated_by'])
            return db_vendor
        except Exception as e:
            await self.db_session.rollback()
            raise DatabaseException(f"Error creating vendor: {str(e)}")

    async def get_vendor_by_id(self, vendor_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[VendorModel]:
        stmt = select(VendorModel).options(
            selectinload(VendorModel.organization),
            selectinload(VendorModel.created_by).selectinload(User.roles).selectinload(Role.permissions),
            selectinload(VendorModel.updated_by).selectinload(User.roles).selectinload(Role.permissions)
        ).where(
            VendorModel.id == vendor_id, 
            VendorModel.organization_id == organization_id
        )
        result = await self.db_session.execute(stmt)
        vendor = result.scalars().first()
        if not vendor:
            raise NotFoundError(f"Vendor with ID {vendor_id} not found in your organization.")
        return vendor

    async def get_all_vendors(self, organization_id: uuid.UUID, skip: int = 0, limit: int = 100, sort_by: Optional[str] = None, sort_order: Optional[str] = "asc") -> Sequence[VendorModel]:
        query = select(VendorModel).options(
            selectinload(VendorModel.organization),
            selectinload(VendorModel.created_by).selectinload(User.roles).selectinload(Role.permissions),
            selectinload(VendorModel.updated_by).selectinload(User.roles).selectinload(Role.permissions)
        ).where(VendorModel.organization_id == organization_id, VendorModel.is_active == True)
        
        if sort_by:
            column = getattr(VendorModel, sort_by, None)
            if column:
                if sort_order.lower() == "desc":
                    query = query.order_by(column.desc())
                else:
                    query = query.order_by(column.asc())
            else:
                # Default sort if sort_by is invalid, or raise error
                query = query.order_by(VendorModel.name.asc())
        else:
            query = query.order_by(VendorModel.name.asc())
            
        query = query.offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def count_vendors(self, organization_id: uuid.UUID) -> int:
        query = select(func.count(VendorModel.id)).where(VendorModel.organization_id == organization_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none() or 0

    async def update_vendor(self, vendor_id: uuid.UUID, vendor_data: VendorUpdate, current_user_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[VendorModel]:
        db_vendor = await self.get_vendor_by_id(vendor_id, organization_id)
        if not db_vendor:
            # Should be caught by get_vendor_by_id, but defensive check
            raise NotFoundError(f"Vendor with ID {vendor_id} not found.")
        
        if not db_vendor.is_active:
            # Or if using is_deleted, check db_vendor.is_deleted
            raise UnprocessableEntityException(f"Vendor with ID {vendor_id} is inactive and cannot be updated.")

        update_payload = vendor_data.model_dump(exclude_unset=True)

        if "name" in update_payload and update_payload["name"] != db_vendor.name:
            name_check_stmt = select(VendorModel).where(
                VendorModel.name == update_payload["name"],
                VendorModel.organization_id == organization_id,
                VendorModel.id != vendor_id, # Exclude current vendor
                VendorModel.is_active == True # Or is_deleted == False
            )
            existing_vendor_with_name = await self.db_session.execute(name_check_stmt)
            if existing_vendor_with_name.scalars().first():
                raise ConflictException(f"A vendor with the name '{update_payload['name']}' already exists in your organization.")

        for field, value in update_payload.items():
            if hasattr(db_vendor, field):
                setattr(db_vendor, field, value)
        
        db_vendor.updated_by_id = current_user_id
        # db_vendor.updated_at will be handled by SQLAlchemy's onupdate if configured, otherwise set manually
        # db_vendor.updated_at = datetime.utcnow() 

        try:
            await self.db_session.commit()
            await self.db_session.refresh(db_vendor)
            await self.db_session.refresh(db_vendor, attribute_names=['organization', 'created_by', 'updated_by'])
            return db_vendor
        except Exception as e:
            await self.db_session.rollback()
            raise DatabaseException(f"Error updating vendor: {str(e)}")

    async def delete_vendor(self, vendor_id: uuid.UUID, current_user_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[VendorModel]:
        db_vendor = await self.get_vendor_by_id(vendor_id, organization_id)
        if not db_vendor:
            raise NotFoundError(f"Vendor with ID {vendor_id} not found.")

        if not db_vendor.is_active: # Already inactive
            return db_vendor # Or raise an error if trying to delete an already inactive one

        db_vendor.is_active = False
        db_vendor.updated_by_id = current_user_id
        # db_vendor.updated_at = datetime.utcnow() # If not handled by onupdate
        # If using is_deleted and deleted_at:
        # db_vendor.is_deleted = True
        # db_vendor.deleted_at = datetime.utcnow()

        try:
            await self.db_session.commit()
            await self.db_session.refresh(db_vendor)
            await self.db_session.refresh(db_vendor, attribute_names=['organization', 'created_by', 'updated_by'])
            return db_vendor
        except Exception as e:
            await self.db_session.rollback()
            raise DatabaseException(f"Error deleting vendor: {str(e)}")
