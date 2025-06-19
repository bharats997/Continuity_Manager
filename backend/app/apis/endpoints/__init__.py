# backend/app/apis/endpoints/__init__.py
from fastapi import APIRouter

from . import applications
from . import departments
from . import locations
from . import roles
from . import users
from . import vendors
from . import bia_categories
from . import bia_parameters

api_router = APIRouter()

api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])
api_router.include_router(bia_categories.router, prefix="/bia_categories", tags=["BIA Categories"])

# Include BIA Parameter routers
api_router.include_router(bia_parameters.router_impact_scales)
api_router.include_router(bia_parameters.router_timeframes)
