"""change_id_columns_to_uuid_char36

Revision ID: 0a68b7c32f1f
Revises: 2d8017da1a34
Create Date: 2025-06-04 17:16:21.000000

"""
import os
import sys

# Add project root to sys.path to allow for absolute imports from backend
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy import inspect

# import backend.app.database.custom_types # For SQLiteUUID

# revision identifiers, used by Alembic.
revision: str = '0a68b7c32f1f'
down_revision: Union[str, None] = '2d8017da1a34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define SQLiteUUID type for convenience
# SQLiteUUID = backend.app.database.custom_types.SQLiteUUID

# List of foreign key constraints to manage
constraints_to_manage = [
    # From initial_migration (f6728996b67c)
    {'type': 'explicit', 'name_arg': 'fk_departments_organizationId_organizations', 'table': 'departments', 'columns': ['organizationId'], 'ref_table': 'organizations', 'ref_columns': ['id'], 'ondelete': 'CASCADE'},
    {'type': 'explicit', 'name_arg': 'fk_departments_department_head_id_people', 'table': 'departments', 'columns': ['department_head_id'], 'ref_table': 'people', 'ref_columns': ['id'], 'ondelete': 'SET NULL'},
    {'type': 'explicit', 'name_arg': 'fk_locations_organizationId_organizations', 'table': 'locations', 'columns': ['organizationId'], 'ref_table': 'organizations', 'ref_columns': ['id'], 'ondelete': 'CASCADE'},
    {'type': 'explicit', 'name_arg': 'fk_people_organizationId_organizations', 'table': 'people', 'columns': ['organizationId'], 'ref_table': 'organizations', 'ref_columns': ['id'], 'ondelete': 'CASCADE'},
    {'type': 'explicit', 'name_arg': 'fk_people_departmentId_departments', 'table': 'people', 'columns': ['departmentId'], 'ref_table': 'departments', 'ref_columns': ['id'], 'ondelete': 'SET NULL'},
    {'type': 'explicit', 'name_arg': 'fk_people_locationId_locations', 'table': 'people', 'columns': ['locationId'], 'ref_table': 'locations', 'ref_columns': ['id'], 'ondelete': 'SET NULL'},
    {'type': 'explicit', 'name_arg': 'fk_department_locations_association_department_id_departments', 'table': 'department_locations_association', 'columns': ['department_id'], 'ref_table': 'departments', 'ref_columns': ['id'], 'ondelete': 'CASCADE'},
    {'type': 'explicit', 'name_arg': 'fk_department_locations_association_location_id_locations', 'table': 'department_locations_association', 'columns': ['location_id'], 'ref_table': 'locations', 'ref_columns': ['id'], 'ondelete': 'CASCADE'},
    # Added for people.createdBy, people.updatedBy
    {'type': 'explicit', 'name_arg': 'fk_people_createdBy_people', 'table': 'people', 'columns': ['createdBy'], 'ref_table': 'people', 'ref_columns': ['id'], 'ondelete': 'SET NULL'},
    {'type': 'explicit', 'name_arg': 'fk_people_updatedBy_people', 'table': 'people', 'columns': ['updatedBy'], 'ref_table': 'people', 'ref_columns': ['id'], 'ondelete': 'SET NULL'},
    # Added for departments.createdBy, departments.updatedBy
    {'type': 'explicit', 'name_arg': 'fk_departments_createdBy_people', 'table': 'departments', 'columns': ['createdBy'], 'ref_table': 'people', 'ref_columns': ['id'], 'ondelete': 'SET NULL'},
    {'type': 'explicit', 'name_arg': 'fk_departments_updatedBy_people', 'table': 'departments', 'columns': ['updatedBy'], 'ref_table': 'people', 'ref_columns': ['id'], 'ondelete': 'SET NULL'},

    # From rbac_migration (26b9f71a97eb)
    {'type': 'op_f', 'name_arg': 'fk_people_roles_personId_people', 'table': 'people_roles', 'columns': ['personId'], 'ref_table': 'people', 'ref_columns': ['id'], 'ondelete': 'CASCADE'},
    {'type': 'op_f', 'name_arg': 'fk_people_roles_roleId_roles', 'table': 'people_roles', 'columns': ['roleId'], 'ref_table': 'roles', 'ref_columns': ['id'], 'ondelete': 'CASCADE'},
    {'type': 'op_f', 'name_arg': 'fk_role_permissions_permission_id_permissions', 'table': 'role_permissions', 'columns': ['permission_id'], 'ref_table': 'permissions', 'ref_columns': ['id'], 'ondelete': 'CASCADE'},
    {'type': 'op_f', 'name_arg': 'fk_role_permissions_role_id_roles', 'table': 'role_permissions', 'columns': ['role_id'], 'ref_table': 'roles', 'ref_columns': ['id'], 'ondelete': 'CASCADE'},
    
    # From applications_migration (d9f76c4a13d7)
    {'type': 'op_f', 'name_arg': 'fk_applications_organizationId_organizations', 'table': 'applications', 'columns': ['organizationId'], 'ref_table': 'organizations', 'ref_columns': ['id'], 'ondelete': 'CASCADE'},
    {'type': 'op_f', 'name_arg': 'fk_applications_appOwnerId_people', 'table': 'applications', 'columns': ['appOwnerId'], 'ref_table': 'people', 'ref_columns': ['id'], 'ondelete': 'SET NULL'},
    {'type': 'op_f', 'name_arg': 'fk_applications_createdBy_people', 'table': 'applications', 'columns': ['createdBy'], 'ref_table': 'people', 'ref_columns': ['id'], 'ondelete': 'SET NULL'},
    {'type': 'op_f', 'name_arg': 'fk_applications_updatedBy_people', 'table': 'applications', 'columns': ['updatedBy'], 'ref_table': 'people', 'ref_columns': ['id'], 'ondelete': 'SET NULL'},
    {'type': 'op_f', 'name_arg': 'fk_applications_deletedBy_people', 'table': 'applications', 'columns': ['deletedBy'], 'ref_table': 'people', 'ref_columns': ['id'], 'ondelete': 'SET NULL'},
    
    # Constraint for roles.organization_id (FK from model, column added in this migration)
    {'type': 'op_f', 'name_arg': 'fk_roles_organization_id_organizations', 'table': 'roles', 'columns': ['organization_id'], 'ref_table': 'organizations', 'ref_columns': ['id'], 'ondelete': 'NO ACTION'},
]

def get_constraint_name_for_op(constraint_def):
    if constraint_def['type'] == 'explicit':
        return constraint_def['name_arg']
    return op.f(constraint_def['name_arg'])

def column_exists(op_ctx, table_name, column_name):
    bind = op_ctx.get_bind()
    inspector = inspect(bind)
    columns = inspector.get_columns(table_name)
    return any(c['name'] == column_name for c in columns)

def upgrade() -> None:
    op.execute("SET foreign_key_checks = 0;")
    try:
        # 1. Drop constraints
        for const_def in constraints_to_manage:
            constraint_name = get_constraint_name_for_op(const_def)
            try:
                op.drop_constraint(constraint_name, const_def['table'], type_='foreignkey')
            except Exception as e:
                print(f"Info: Could not drop constraint {constraint_name} on table {const_def['table']}. Error: {e}")

        # 2. Drop unique constraint
        try:
            op.drop_index(op.f('uq_person_organization_email'), table_name='people')
        except Exception as e:
            print(f"Info: Could not drop unique constraint uq_person_organization_email. Error: {e}")

        # 3. Add new columns
        if not column_exists(op, 'applications', 'status'):
            op.add_column('applications', sa.Column('status', sa.Enum('DEVELOPMENT', 'BETA', 'ACTIVE', 'INACTIVE', 'DECOMMISSIONED', name='application_status_enum'), nullable=False, server_default='ACTIVE'))
        if not column_exists(op, 'applications', 'is_deleted'):
            op.add_column('applications', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))
        if not column_exists(op, 'roles', 'organization_id'):
            op.add_column('roles', sa.Column('organization_id', SQLiteUUID(), nullable=False)) # Created as CHAR(36) NOT NULL

        # 4. Alter Primary Key 'id' columns to CHAR(36) NOT NULL using raw SQL
        op.execute("ALTER TABLE organizations MODIFY id CHAR(36) NOT NULL;")
        op.execute("ALTER TABLE people MODIFY id CHAR(36) NOT NULL;")
        op.execute("ALTER TABLE departments MODIFY id CHAR(36) NOT NULL;")
        op.execute("ALTER TABLE locations MODIFY id CHAR(36) NOT NULL;")
        op.execute("ALTER TABLE applications MODIFY id CHAR(36) NOT NULL;")
        op.execute("ALTER TABLE roles MODIFY id CHAR(36) NOT NULL;")
        op.execute("ALTER TABLE permissions MODIFY id CHAR(36) NOT NULL;")

        # 5. Alter Foreign Key columns to CHAR(36) using raw SQL
        op.execute("ALTER TABLE applications MODIFY organizationId CHAR(36) NOT NULL;")
        op.execute("ALTER TABLE applications MODIFY appOwnerId CHAR(36) NULL;")
        op.execute("ALTER TABLE applications MODIFY createdBy CHAR(36) NULL;")
        op.execute("ALTER TABLE applications MODIFY updatedBy CHAR(36) NULL;")
        op.execute("ALTER TABLE applications MODIFY deletedBy CHAR(36) NULL;")

        op.execute("ALTER TABLE department_locations_association MODIFY department_id CHAR(36) NOT NULL;")
        op.execute("ALTER TABLE department_locations_association MODIFY location_id CHAR(36) NOT NULL;")

        op.execute("ALTER TABLE departments MODIFY organizationId CHAR(36) NOT NULL;")
        op.execute("ALTER TABLE departments MODIFY createdBy CHAR(36) NULL;")
        op.execute("ALTER TABLE departments MODIFY updatedBy CHAR(36) NULL;")
        op.execute("ALTER TABLE departments MODIFY department_head_id CHAR(36) NULL;")

        op.execute("ALTER TABLE locations MODIFY organizationId CHAR(36) NOT NULL;")

        op.execute("ALTER TABLE people MODIFY organizationId CHAR(36) NOT NULL;")
        op.execute("ALTER TABLE people MODIFY departmentId CHAR(36) NULL;")
        op.execute("ALTER TABLE people MODIFY locationId CHAR(36) NULL;")
        op.execute("ALTER TABLE people MODIFY createdBy CHAR(36) NULL;")
        op.execute("ALTER TABLE people MODIFY updatedBy CHAR(36) NULL;")

        op.execute("ALTER TABLE people_roles MODIFY personId CHAR(36) NOT NULL;")
        op.execute("ALTER TABLE people_roles MODIFY roleId CHAR(36) NOT NULL;")

        op.execute("ALTER TABLE role_permissions MODIFY role_id CHAR(36) NOT NULL;")
        op.execute("ALTER TABLE role_permissions MODIFY permission_id CHAR(36) NOT NULL;")
        # roles.organization_id is already CHAR(36) NOT NULL due to add_column

        # 6. Adjust timestamp columns (can use op.alter_column)
        op.alter_column('departments', 'createdAt', existing_type=mysql.DATETIME(), nullable=True, existing_server_default=sa.text('(now())'))
        # ... (all other timestamp alterations remain the same)
        op.alter_column('departments', 'updatedAt', existing_type=mysql.DATETIME(), nullable=True, existing_server_default=sa.text('(now())'))
        op.alter_column('organizations', 'createdAt', existing_type=mysql.DATETIME(), nullable=True, existing_server_default=sa.text('(now())'))
        op.alter_column('organizations', 'updatedAt', existing_type=mysql.DATETIME(), nullable=True, existing_server_default=sa.text('(now())'))
        op.alter_column('people', 'createdAt', existing_type=mysql.DATETIME(), nullable=True, existing_server_default=sa.text('(now())'))
        op.alter_column('people', 'updatedAt', existing_type=mysql.DATETIME(), nullable=True, existing_server_default=sa.text('(now())'))
        op.alter_column('people_roles', 'createdAt', existing_type=mysql.DATETIME(), nullable=True, existing_server_default=sa.text('(now())'))
        op.alter_column('permissions', 'createdAt', existing_type=mysql.DATETIME(), nullable=True, existing_server_default=sa.text('(now())'))
        op.alter_column('permissions', 'updatedAt', existing_type=mysql.DATETIME(), nullable=True, existing_server_default=sa.text('(now())'))
        op.alter_column('roles', 'createdAt', existing_type=mysql.DATETIME(), nullable=True, existing_server_default=sa.text('(now())'))
        op.alter_column('roles', 'updatedAt', existing_type=mysql.DATETIME(), nullable=True, existing_server_default=sa.text('(now())'))

        # 7. Index management and column drops
        if column_exists(op, 'applications', 'isActive'):
            op.drop_column('applications', 'isActive')

        try: op.drop_index(op.f('ix_applications_name'), table_name='applications')
        except Exception as e: print(f"Info: Could not drop index ix_applications_name. Error: {e}")
        op.create_index(op.f('ix_applications_name'), 'applications', ['name'], unique=True)
        
        op.create_index(op.f('ix_applications_createdBy'), 'applications', ['createdBy'], unique=False)
        op.create_index(op.f('ix_applications_deletedBy'), 'applications', ['deletedBy'], unique=False)
        op.create_index(op.f('ix_applications_is_deleted'), 'applications', ['is_deleted'], unique=False)
        op.create_index(op.f('ix_applications_status'), 'applications', ['status'], unique=False)
        op.create_index(op.f('ix_applications_updatedBy'), 'applications', ['updatedBy'], unique=False)

        op.create_unique_constraint(op.f('uq_person_organization_email'), 'people', ['organizationId', 'email'])

        try: op.drop_index(op.f('ix_permissions_name'), table_name='permissions')
        except Exception as e: print(f"Info: Could not drop index ix_permissions_name. Error: {e}")
        op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=True)

        op.create_index(op.f('ix_roles_organization_id'), 'roles', ['organization_id'], unique=False)

        # 8. Recreate constraints
        for const_def in constraints_to_manage:
            constraint_name = get_constraint_name_for_op(const_def)
            op.create_foreign_key(
                constraint_name,
                const_def['table'],
                const_def['ref_table'],
                const_def['columns'],
                const_def['ref_columns'],
                ondelete=const_def.get('ondelete')
            )
    finally:
        op.execute("SET foreign_key_checks = 1;")

def downgrade() -> None:
    op.execute("SET foreign_key_checks = 0;")
    try:
        # 1. Drop constraints
        for const_def in constraints_to_manage:
            constraint_name = get_constraint_name_for_op(const_def)
            try:
                op.drop_constraint(constraint_name, const_def['table'], type_='foreignkey')
            except Exception as e:
                print(f"Info: Could not drop constraint {constraint_name} on table {const_def['table']} (downgrade). Error: {e}")
        
        # 2. Drop unique constraint
        try:
            op.drop_index(op.f('uq_person_organization_email'), table_name='people')
        except Exception as e:
            print(f"Info: Could not drop unique constraint uq_person_organization_email (downgrade). Error: {e}")

        # 3. Alter Foreign Key columns back to INTEGER using raw SQL
        op.execute("ALTER TABLE applications MODIFY organizationId INTEGER NOT NULL;")
        op.execute("ALTER TABLE applications MODIFY appOwnerId INTEGER NULL;")
        op.execute("ALTER TABLE applications MODIFY createdBy INTEGER NULL;")
        op.execute("ALTER TABLE applications MODIFY updatedBy INTEGER NULL;")
        op.execute("ALTER TABLE applications MODIFY deletedBy INTEGER NULL;")

        op.execute("ALTER TABLE department_locations_association MODIFY department_id INTEGER NOT NULL;")
        op.execute("ALTER TABLE department_locations_association MODIFY location_id INTEGER NOT NULL;")

        op.execute("ALTER TABLE departments MODIFY organizationId INTEGER NOT NULL;")
        op.execute("ALTER TABLE departments MODIFY createdBy INTEGER NULL;")
        op.execute("ALTER TABLE departments MODIFY updatedBy INTEGER NULL;")
        op.execute("ALTER TABLE departments MODIFY department_head_id INTEGER NULL;")

        op.execute("ALTER TABLE locations MODIFY organizationId INTEGER NOT NULL;")

        op.execute("ALTER TABLE people MODIFY organizationId INTEGER NOT NULL;")
        op.execute("ALTER TABLE people MODIFY departmentId INTEGER NULL;")
        op.execute("ALTER TABLE people MODIFY locationId INTEGER NULL;")
        op.execute("ALTER TABLE people MODIFY createdBy INTEGER NULL;")
        op.execute("ALTER TABLE people MODIFY updatedBy INTEGER NULL;")

        op.execute("ALTER TABLE people_roles MODIFY personId INTEGER NOT NULL;")
        op.execute("ALTER TABLE people_roles MODIFY roleId INTEGER NOT NULL;")

        op.execute("ALTER TABLE role_permissions MODIFY role_id INTEGER NOT NULL;")
        op.execute("ALTER TABLE role_permissions MODIFY permission_id INTEGER NOT NULL;")
        
        # roles.organization_id will be CHAR(36) NOT NULL before being dropped.
        # It needs to be altered to INTEGER if we were keeping it, but it's dropped in step 6.
        # However, if any FKs depend on it being INTEGER *before* it's dropped, we might need to alter it.
        # The FK fk_roles_organization_id_organizations is dropped in step 1. No other FKs should depend on its type after that.
        # Let's alter it to INTEGER for consistency before it's dropped, in case of complex dependencies not immediately obvious.
        if column_exists(op, 'roles', 'organization_id'): # Check existence before altering
             op.execute("ALTER TABLE roles MODIFY organization_id INTEGER NOT NULL;")

        # 4. Alter Primary Key 'id' columns back to INTEGER using raw SQL
        op.execute("ALTER TABLE organizations MODIFY id INTEGER NOT NULL;")
        op.execute("ALTER TABLE people MODIFY id INTEGER NOT NULL;")
        op.execute("ALTER TABLE departments MODIFY id INTEGER NOT NULL;")
        op.execute("ALTER TABLE locations MODIFY id INTEGER NOT NULL;")
        op.execute("ALTER TABLE applications MODIFY id INTEGER NOT NULL;")
        op.execute("ALTER TABLE roles MODIFY id INTEGER NOT NULL;")
        op.execute("ALTER TABLE permissions MODIFY id INTEGER NOT NULL;")

        # 5. Revert timestamp columns
        op.alter_column('roles', 'updatedAt', existing_type=mysql.DATETIME(), nullable=False, existing_server_default=sa.text('(now())'))
        # ... (all other timestamp alterations remain the same)
        op.alter_column('roles', 'createdAt', existing_type=mysql.DATETIME(), nullable=False, existing_server_default=sa.text('(now())'))
        op.alter_column('permissions', 'updatedAt', existing_type=mysql.DATETIME(), nullable=False, existing_server_default=sa.text('(now())'))
        op.alter_column('permissions', 'createdAt', existing_type=mysql.DATETIME(), nullable=False, existing_server_default=sa.text('(now())'))
        op.alter_column('people_roles', 'createdAt', existing_type=mysql.DATETIME(), nullable=False, existing_server_default=sa.text('(now())'))
        op.alter_column('people', 'updatedAt', existing_type=mysql.DATETIME(), nullable=False, existing_server_default=sa.text('(now())'))
        op.alter_column('people', 'createdAt', existing_type=mysql.DATETIME(), nullable=False, existing_server_default=sa.text('(now())'))
        op.alter_column('organizations', 'updatedAt', existing_type=mysql.DATETIME(), nullable=False, existing_server_default=sa.text('(now())'))
        op.alter_column('organizations', 'createdAt', existing_type=mysql.DATETIME(), nullable=False, existing_server_default=sa.text('(now())'))
        op.alter_column('departments', 'updatedAt', existing_type=mysql.DATETIME(), nullable=False, existing_server_default=sa.text('(now())'))
        op.alter_column('departments', 'createdAt', existing_type=mysql.DATETIME(), nullable=False, existing_server_default=sa.text('(now())'))

        # 6. Drop new columns / restore old columns
        try: op.drop_index(op.f('ix_roles_organization_id'), table_name='roles')
        except Exception as e: print(f"Info: Could not drop index ix_roles_organization_id (downgrade). Error: {e}")
        if column_exists(op, 'roles', 'organization_id'):
            op.drop_column('roles', 'organization_id')

        if not column_exists(op, 'applications', 'isActive'):
            op.add_column('applications', sa.Column('isActive', mysql.TINYINT(display_width=1), server_default=sa.text("'1'"), autoincrement=False, nullable=False))
        
        # ... (index drops for applications table)
        try: op.drop_index(op.f('ix_applications_updatedBy'), table_name='applications')
        except: pass
        try: op.drop_index(op.f('ix_applications_status'), table_name='applications')
        except: pass
        try: op.drop_index(op.f('ix_applications_is_deleted'), table_name='applications')
        except: pass
        try: op.drop_index(op.f('ix_applications_deletedBy'), table_name='applications')
        except: pass
        # ix_applications_createdBy was missing, added now
        try: op.drop_index(op.f('ix_applications_createdBy'), table_name='applications')
        except: pass
        try: op.drop_index(op.f('ix_applications_name'), table_name='applications')
        except: pass
        op.create_index(op.f('ix_applications_name'), 'applications', ['name'], unique=False)
            
        if column_exists(op, 'applications', 'is_deleted'):
            op.drop_column('applications', 'is_deleted')
        if column_exists(op, 'applications', 'status'):
            op.drop_column('applications', 'status')
        
        try: op.drop_index(op.f('ix_permissions_name'), table_name='permissions')
        except: pass
        op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=False)

        # 7. Recreate unique constraint for people table with INTEGER type
        op.create_unique_constraint(op.f('uq_person_organization_email'), 'people', ['organizationId', 'email'])

        # 8. Recreate constraints
        for const_def in constraints_to_manage:
            constraint_name = get_constraint_name_for_op(const_def)
            op.create_foreign_key(
                constraint_name,
                const_def['table'],
                const_def['ref_table'],
                const_def['columns'],
                const_def['ref_columns'],
                ondelete=const_def.get('ondelete')
            )
    finally:
        op.execute("SET foreign_key_checks = 1;")
