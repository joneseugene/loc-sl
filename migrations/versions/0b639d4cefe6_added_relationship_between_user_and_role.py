"""Added relationship between User and Role

Revision ID: 0b639d4cefe6
Revises: 7e0fb6253be9
Create Date: 2025-02-17 13:56:36.220130

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b639d4cefe6'
down_revision: Union[str, None] = '7e0fb6253be9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
