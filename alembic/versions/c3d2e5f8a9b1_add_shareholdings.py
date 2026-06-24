"""add shareholdings table

Revision ID: c3d2e5f8a9b1
Revises: b2f1a7c9d3e4
Create Date: 2026-06-24 13:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d2e5f8a9b1'
down_revision: Union[str, Sequence[str], None] = 'b2f1a7c9d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'shareholdings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('period', sa.String(length=16), nullable=False),
        sa.Column('period_date', sa.Date(), nullable=False),
        sa.Column('promoter_pct', sa.Float(), nullable=True),
        sa.Column('public_pct', sa.Float(), nullable=True),
        sa.Column('fii_pct', sa.Float(), nullable=True),
        sa.Column('dii_pct', sa.Float(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'period_date', name='uq_shp_company_period'),
    )
    op.create_index(op.f('ix_shareholdings_company_id'), 'shareholdings', ['company_id'])
    op.create_index(op.f('ix_shareholdings_period_date'), 'shareholdings', ['period_date'])


def downgrade() -> None:
    op.drop_index(op.f('ix_shareholdings_period_date'), table_name='shareholdings')
    op.drop_index(op.f('ix_shareholdings_company_id'), table_name='shareholdings')
    op.drop_table('shareholdings')
