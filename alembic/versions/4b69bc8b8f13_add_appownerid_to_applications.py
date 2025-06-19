"""add_appownerid_to_applications

Revision ID: 4b69bc8b8f13
Revises: d9f76c4a13d7
Create Date: 2025-05-31 21:01:05.813396

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b69bc8b8f13'
down_revision: Union[str, None] = 'd9f76c4a13d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
