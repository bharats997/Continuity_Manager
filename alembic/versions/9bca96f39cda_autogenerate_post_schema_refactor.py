"""autogenerate_post_schema_refactor

Revision ID: 9bca96f39cda
Revises: 8a1b258ce0b8
Create Date: 2025-06-13 20:00:46.531727

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9bca96f39cda'
down_revision: Union[str, None] = '8a1b258ce0b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
