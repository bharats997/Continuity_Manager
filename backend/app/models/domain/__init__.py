# backend/app/models/domain/__init__.py
from .organizations import Organization
from .departments import Department
from .locations import Location
from .applications import Application
from .roles import Role
from .people import Person, people_roles_association # people_roles_association is also needed by Base.metadata
from .permissions import Permission, role_permissions_association # Ensure Alembic detects these
