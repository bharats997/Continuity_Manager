"""add_appownerid_to_applications

Revision ID: 80e65dd55c52
Revises: 4b69bc8b8f13
Create Date: 2025-05-31 21:03:36.301582

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '80e65dd55c52'
down_revision: Union[str, None] = '4b69bc8b8f13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
