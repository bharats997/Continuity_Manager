"""rename_applicationType_to_type_and_update_enum_in_applications

Revision ID: 65e32ec2bf46
Revises: 9bca96f39cda
Create Date: 2025-06-16 16:48:16.874111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '65e32ec2bf46'
down_revision: Union[str, None] = '9bca96f39cda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define the ENUM type for use in upgrade and downgrade
application_type_enum = sa.Enum('SaaS', 'Owned', name='application_type_enum')


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Alter the existing 'type' column to the correct ENUM definition and NOT NULL.
    #    This assumes the 'type' column already exists due to the previous 'Duplicate column' error.
    op.alter_column('applications', 'type',
               type_=application_type_enum,
               nullable=False,
               existing_type=mysql.VARCHAR(255),  # Plausible existing type if it's not already ENUM
               existing_nullable=True)         # Plausible existing nullability

    # 2. Drop the 'applicationType' column if it exists.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('applications')
    if any(c['name'] == 'applicationType' for c in columns):
        op.drop_column('applications', 'applicationType')


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Add 'applicationType' back as VARCHAR(100), nullable=True, if it doesn't exist.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('applications')
    if not any(c['name'] == 'applicationType' for c in columns):
        op.add_column('applications', sa.Column('applicationType', mysql.VARCHAR(100), nullable=True))
    # else: # Optionally, ensure its type if it exists
        # op.alter_column('applications', 'applicationType', type_=mysql.VARCHAR(100), nullable=True, existing_type=application_type_enum)

    # 2. Drop the 'type' column if it exists.
    if any(c['name'] == 'type' for c in columns):
        op.drop_column('applications', 'type')
