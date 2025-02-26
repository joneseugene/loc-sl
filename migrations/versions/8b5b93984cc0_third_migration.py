"""Third Migration

Revision ID: 8b5b93984cc0
Revises: fb8796515379
Create Date: 2025-02-26 12:13:49.695103

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b5b93984cc0'
down_revision: Union[str, None] = 'fb8796515379'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('roles', sa.Column('slug', sa.String(), nullable=True))
    op.create_index(op.f('ix_roles_slug'), 'roles', ['slug'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_roles_slug'), table_name='roles')
    op.drop_column('roles', 'slug')
    # ### end Alembic commands ###
