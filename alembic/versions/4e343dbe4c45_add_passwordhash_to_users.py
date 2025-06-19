"""add_passwordhash_to_users

Revision ID: 4e343dbe4c45
Revises: d1d332415966
Create Date: 2025-06-10 11:59:28.286840

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e343dbe4c45'
down_revision: Union[str, None] = 'd1d332415966'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('passwordHash', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'passwordHash')
