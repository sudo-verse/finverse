"""add deals table

Revision ID: f6a5b8c3d9e2
Revises: e5f4a7b2c8d1
Create Date: 2026-06-25 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a5b8c3d9e2'
down_revision: Union[str, Sequence[str], None] = 'e5f4a7b2c8d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'deals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deal_date', sa.Date(), nullable=False),
        sa.Column('deal_type', sa.String(length=8), nullable=False),
        sa.Column('symbol', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('client_name', sa.String(length=255), nullable=True),
        sa.Column('side', sa.String(length=4), nullable=True),
        sa.Column('quantity', sa.BigInteger(), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('remarks', sa.String(length=255), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('deal_date', 'deal_type', 'symbol', 'client_name', 'side',
                            'quantity', name='uq_deal_natural'),
    )
    op.create_index(op.f('ix_deals_deal_date'), 'deals', ['deal_date'])
    op.create_index(op.f('ix_deals_symbol'), 'deals', ['symbol'])


def downgrade() -> None:
    op.drop_index(op.f('ix_deals_symbol'), table_name='deals')
    op.drop_index(op.f('ix_deals_deal_date'), table_name='deals')
    op.drop_table('deals')
