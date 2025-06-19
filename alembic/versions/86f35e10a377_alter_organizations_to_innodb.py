"""alter_organizations_to_innodb

Revision ID: 86f35e10a377
Revises: 26b9f71a97eb
Create Date: 2025-05-30 19:08:28.827844

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86f35e10a377'
down_revision: Union[str, None] = '26b9f71a97eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # If you know the original engine and want to revert, you can specify it here.
    # For example: op.execute('ALTER TABLE organizations ENGINE=MyISAM')
    # For now, we'll just pass as reverting engine can be complex.
    pass
    pass
