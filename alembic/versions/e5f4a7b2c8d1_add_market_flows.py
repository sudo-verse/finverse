"""add market_flows table

Revision ID: e5f4a7b2c8d1
Revises: d4e3f6a1b2c5
Create Date: 2026-06-25 18:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f4a7b2c8d1'
down_revision: Union[str, Sequence[str], None] = 'd4e3f6a1b2c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'market_flows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('fii_buy', sa.Float(), nullable=True),
        sa.Column('fii_sell', sa.Float(), nullable=True),
        sa.Column('fii_net', sa.Float(), nullable=True),
        sa.Column('dii_buy', sa.Float(), nullable=True),
        sa.Column('dii_sell', sa.Float(), nullable=True),
        sa.Column('dii_net', sa.Float(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', name='uq_market_flow_date'),
    )
    op.create_index(op.f('ix_market_flows_date'), 'market_flows', ['date'])


def downgrade() -> None:
    op.drop_index(op.f('ix_market_flows_date'), table_name='market_flows')
    op.drop_table('market_flows')
