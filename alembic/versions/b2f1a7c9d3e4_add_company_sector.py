"""add company.sector

Revision ID: b2f1a7c9d3e4
Revises: 4441cb12cadd
Create Date: 2026-06-24 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2f1a7c9d3e4'
down_revision: Union[str, Sequence[str], None] = '4441cb12cadd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('companies', sa.Column('sector', sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column('companies', 'sector')
