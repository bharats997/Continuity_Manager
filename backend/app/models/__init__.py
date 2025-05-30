# backend/app/models/__init__.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, ForeignKey

# Define the shared Base for all models in this package
Base = declarative_base()

# Association table for Person and Role (many-to-many)
# Note: ForeignKey targets (e.g., 'persons.id', 'roles.id')
# are placeholders. We will confirm and adjust these based on the
# actual __tablename__ attributes in person.py and role.py.
user_roles_table = Table('user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('persons.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

# Association table for Role and Permission (many-to-many)
# Note: ForeignKey targets (e.g., 'roles.id', 'permissions.id')
# are placeholders. We will confirm and adjust these based on the
# actual __tablename__ attributes in role.py and permission.py.
role_permissions_table = Table('role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

# Imports for SQLAlchemy model classes
from .person import Person  # Imports the SQLAlchemy Person model
from .role import Role      # Imports the SQLAlchemy Role model
from .permission import Permission  # Imports the SQLAlchemy Permission model

# It's also good practice to define __all__ if this package is meant to be
# imported with *, though it's not strictly necessary for Alembic/SQLAlchemy discovery here.
__all__ = [
    'Base',
    'user_roles_table',
    'role_permissions_table',
    'Person',
    'Role',
    'Permission'
]
