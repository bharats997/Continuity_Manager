"""add_appownerid_to_applications_attempt_4

Revision ID: 2d8017da1a34
Revises: 80e65dd55c52
Create Date: 2025-05-31 21:10:46.130121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d8017da1a34'
down_revision: Union[str, None] = '80e65dd55c52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The appOwnerId column, its foreign key, and index already exist
    # in the database. This upgrade path is intentionally left empty.
    # We will use 'alembic stamp' to mark this revision as applied.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_applications_appOwnerId'), table_name='applications')
    op.drop_constraint('fk_applications_appOwnerId_people', 'applications', type_='foreignkey')
    op.drop_column('applications', 'appOwnerId')
