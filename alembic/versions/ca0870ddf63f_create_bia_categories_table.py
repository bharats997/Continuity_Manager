"""create_bia_categories_table

Revision ID: ca0870ddf63f
Revises: 3f3782bf2d4a
Create Date: 2025-06-10 12:52:27.231221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca0870ddf63f'
down_revision: Union[str, None] = '3f3782bf2d4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'bia_categories',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_bia_categories_organization_id', ondelete='CASCADE'),
        sa.UniqueConstraint('name', 'organization_id', name='uq_bia_category_name_organization')
    )



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('bia_categories')

