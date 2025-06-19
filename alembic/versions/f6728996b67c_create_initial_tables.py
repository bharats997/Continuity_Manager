"""create_initial_tables

Revision ID: f6728996b67c
Revises: 
Create Date: 2025-05-30 10:57:14.308075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6728996b67c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('organizations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('isActive', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('createdAt', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updatedAt', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)

    op.create_table('locations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address_line1', sa.String(length=255), nullable=False),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state_province', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('organizationId', sa.Integer(), nullable=False),
        sa.Column('isActive', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('createdAt', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updatedAt', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organizationId'], ['organizations.id'], name=op.f('fk_locations_organizationId_organizations'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_locations_id'), 'locations', ['id'], unique=False)
    op.create_index(op.f('ix_locations_name'), 'locations', ['name'], unique=False)
    op.create_index(op.f('ix_locations_organizationId'), 'locations', ['organizationId'], unique=False)

    op.create_table('departments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organizationId', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('isActive', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('createdAt', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updatedAt', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('createdBy', sa.Integer(), nullable=True),
        sa.Column('updatedBy', sa.Integer(), nullable=True),
        sa.Column('department_head_id', sa.Integer(), nullable=True),
        sa.Column('number_of_team_members', sa.Integer(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organizationId'], ['organizations.id'], name=op.f('fk_departments_organizationId_organizations'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_departments_id'), 'departments', ['id'], unique=False)
    op.create_index(op.f('ix_departments_organizationId'), 'departments', ['organizationId'], unique=False)
    op.create_index(op.f('ix_departments_is_deleted'), 'departments', ['is_deleted'], unique=False)

    op.create_table('people',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organizationId', sa.Integer(), nullable=False),
        sa.Column('firstName', sa.String(length=100), nullable=False),
        sa.Column('lastName', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('departmentId', sa.Integer(), nullable=True),
        sa.Column('locationId', sa.Integer(), nullable=True),
        sa.Column('jobTitle', sa.String(length=100), nullable=True),
        sa.Column('isActive', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('createdAt', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updatedAt', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('createdBy', sa.Integer(), nullable=True),
        sa.Column('updatedBy', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['organizationId'], ['organizations.id'], name=op.f('fk_people_organizationId_organizations'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['locationId'], ['locations.id'], name=op.f('fk_people_locationId_locations'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organizationId', 'email', name='uq_person_organization_email'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_people_id'), 'people', ['id'], unique=False)
    op.create_index(op.f('ix_people_organizationId'), 'people', ['organizationId'], unique=False)
    op.create_index(op.f('ix_people_email'), 'people', ['email'], unique=False)
    op.create_index(op.f('ix_people_departmentId'), 'people', ['departmentId'], unique=False)
    op.create_index(op.f('ix_people_locationId'), 'people', ['locationId'], unique=False)

    op.create_foreign_key(op.f('fk_people_departmentId_departments'), 'people', 'departments', ['departmentId'], ['id'], ondelete='SET NULL', use_alter=True)
    op.create_foreign_key(op.f('fk_people_createdBy_people'), 'people', 'people', ['createdBy'], ['id'], ondelete='SET NULL', use_alter=True)
    op.create_foreign_key(op.f('fk_people_updatedBy_people'), 'people', 'people', ['updatedBy'], ['id'], ondelete='SET NULL', use_alter=True)

    op.create_foreign_key(op.f('fk_departments_createdBy_people'), 'departments', 'people', ['createdBy'], ['id'], ondelete='SET NULL', use_alter=True)
    op.create_foreign_key(op.f('fk_departments_updatedBy_people'), 'departments', 'people', ['updatedBy'], ['id'], ondelete='SET NULL', use_alter=True)
    op.create_foreign_key(op.f('fk_departments_department_head_id_people'), 'departments', 'people', ['department_head_id'], ['id'], ondelete='SET NULL', use_alter=True)

    op.create_table('department_locations_association',
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], name=op.f('fk_department_locations_association_department_id_departments'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], name=op.f('fk_department_locations_association_location_id_locations'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('department_id', 'location_id'),
        mysql_engine='InnoDB'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('department_locations_association')

    # Downgrade for 'departments' table FKs (assuming use_alter=True was used for creation)
    op.drop_constraint(op.f('fk_departments_department_head_id_people'), 'departments', type_='foreignkey')
    op.drop_constraint(op.f('fk_departments_updatedBy_people'), 'departments', type_='foreignkey')
    op.drop_constraint(op.f('fk_departments_createdBy_people'), 'departments', type_='foreignkey')

    # Downgrade for 'people' table FKs (assuming use_alter=True was used for creation)
    op.drop_constraint(op.f('fk_people_departmentId_departments'), 'people', type_='foreignkey') # This FK points from people to departments
    op.drop_constraint(op.f('fk_people_createdBy_people'), 'people', type_='foreignkey')
    op.drop_constraint(op.f('fk_people_updatedBy_people'), 'people', type_='foreignkey')
    
    op.drop_index(op.f('ix_people_locationId'), table_name='people')
    op.drop_index(op.f('ix_people_departmentId'), table_name='people')
    op.drop_index(op.f('ix_people_email'), table_name='people')
    op.drop_index(op.f('ix_people_organizationId'), table_name='people')
    op.drop_index(op.f('ix_people_id'), table_name='people')
    op.drop_table('people')

    op.drop_index(op.f('ix_departments_is_deleted'), table_name='departments')
    op.drop_index(op.f('ix_departments_organizationId'), table_name='departments')
    op.drop_index(op.f('ix_departments_id'), table_name='departments')
    op.drop_table('departments')

    op.drop_index(op.f('ix_locations_organizationId'), table_name='locations')
    op.drop_index(op.f('ix_locations_name'), table_name='locations')
    op.drop_index(op.f('ix_locations_id'), table_name='locations')
    op.drop_table('locations')

    op.drop_index(op.f('ix_organizations_name'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')
