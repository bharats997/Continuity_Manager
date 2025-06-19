"""rename_people_roles_to_user_roles_and_columns

Revision ID: 3f3782bf2d4a
Revises: 4e343dbe4c45
Create Date: 2025-06-10 12:42:55.325571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f3782bf2d4a'
down_revision: Union[str, None] = '4e343dbe4c45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == 'mysql':
        op.execute("SET foreign_key_checks = 0;")

    op.execute("DROP TABLE IF EXISTS `user_roles`;")
    op.execute("DROP TABLE IF EXISTS `people_roles`;")

    op.create_table('user_roles',
        sa.Column('user_id', sa.CHAR(length=36), nullable=False),
        sa.Column('role_id', sa.CHAR(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_roles_user_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_user_roles_role_id_roles'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    if bind.dialect.name == 'mysql':
        op.execute("SET foreign_key_checks = 1;")


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == 'mysql':
        op.execute("SET foreign_key_checks = 0;")

    op.drop_table('user_roles')

    if bind.dialect.name == 'mysql':
        op.execute("SET foreign_key_checks = 1;")
