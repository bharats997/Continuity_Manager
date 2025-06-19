"""create_applications_table

Revision ID: d9f76c4a13d7
Revises: 86f35e10a377
Create Date: 2025-05-30 18:58:50.663956

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9f76c4a13d7'
down_revision: Union[str, None] = '86f35e10a377'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('vendor', sa.String(length=255), nullable=True),
        sa.Column('organizationId', sa.Integer(), nullable=False),
        sa.Column('appOwnerId', sa.Integer(), nullable=True),
        sa.Column('applicationType', sa.String(length=100), nullable=True),
        sa.Column('hostingEnvironment', sa.String(length=100), nullable=True),
        sa.Column('criticality', sa.String(length=50), nullable=True),
        sa.Column('isActive', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('createdAt', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updatedAt', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deletedAt', sa.DateTime(timezone=True), nullable=True),
        sa.Column('createdBy', sa.Integer(), nullable=True),
        sa.Column('updatedBy', sa.Integer(), nullable=True),
        sa.Column('deletedBy', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_applications')),
        sa.ForeignKeyConstraint(['organizationId'], ['organizations.id'], name=op.f('fk_applications_organizationId_organizations'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['appOwnerId'], ['people.id'], name=op.f('fk_applications_appOwnerId_people'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['createdBy'], ['people.id'], name=op.f('fk_applications_createdBy_people'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updatedBy'], ['people.id'], name=op.f('fk_applications_updatedBy_people'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deletedBy'], ['people.id'], name=op.f('fk_applications_deletedBy_people'), ondelete='SET NULL'),
        # Ensure InnoDB engine for foreign key support
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_applications_appOwnerId'), 'applications', ['appOwnerId'], unique=False)
    op.create_index(op.f('ix_applications_id'), 'applications', ['id'], unique=False)
    op.create_index(op.f('ix_applications_name'), 'applications', ['name'], unique=False)
    op.create_index(op.f('ix_applications_organizationId'), 'applications', ['organizationId'], unique=False)



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_applications_organizationId'), table_name='applications')
    op.drop_index(op.f('ix_applications_name'), table_name='applications')
    op.drop_index(op.f('ix_applications_id'), table_name='applications')
    op.drop_index(op.f('ix_applications_appOwnerId'), table_name='applications')
    op.drop_table('applications')

