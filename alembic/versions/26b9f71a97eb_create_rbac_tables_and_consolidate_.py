"""Create RBAC tables and consolidate models

Revision ID: 26b9f71a97eb
Revises: f6728996b67c
Create Date: 2025-05-30 15:27:07.868906

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26b9f71a97eb'
down_revision: Union[str, None] = 'f6728996b67c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
