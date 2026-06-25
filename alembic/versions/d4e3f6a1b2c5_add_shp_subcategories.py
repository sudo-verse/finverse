"""add DII sub-category columns to shareholdings

Revision ID: d4e3f6a1b2c5
Revises: c3d2e5f8a9b1
Create Date: 2026-06-25 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e3f6a1b2c5'
down_revision: Union[str, Sequence[str], None] = 'c3d2e5f8a9b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('shareholdings', sa.Column('mf_pct', sa.Float(), nullable=True))
    op.add_column('shareholdings', sa.Column('insurance_pct', sa.Float(), nullable=True))
    op.add_column('shareholdings', sa.Column('banks_pct', sa.Float(), nullable=True))
    op.add_column('shareholdings', sa.Column('pension_pct', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('shareholdings', 'pension_pct')
    op.drop_column('shareholdings', 'banks_pct')
    op.drop_column('shareholdings', 'insurance_pct')
    op.drop_column('shareholdings', 'mf_pct')
