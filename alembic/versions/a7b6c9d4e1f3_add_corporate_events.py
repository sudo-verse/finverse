"""add corporate_events table

Revision ID: a7b6c9d4e1f3
Revises: f6a5b8c3d9e2
Create Date: 2026-06-26 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b6c9d4e1f3'
down_revision: Union[str, Sequence[str], None] = 'f6a5b8c3d9e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'corporate_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('event_type', sa.String(length=16), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('detail', sa.String(length=512), nullable=True),
        sa.Column('source', sa.String(length=16), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'event_date', 'event_type', name='uq_event_natural'),
    )
    op.create_index(op.f('ix_corporate_events_symbol'), 'corporate_events', ['symbol'])
    op.create_index(op.f('ix_corporate_events_event_type'), 'corporate_events', ['event_type'])
    op.create_index(op.f('ix_corporate_events_event_date'), 'corporate_events', ['event_date'])


def downgrade() -> None:
    op.drop_index(op.f('ix_corporate_events_event_date'), table_name='corporate_events')
    op.drop_index(op.f('ix_corporate_events_event_type'), table_name='corporate_events')
    op.drop_index(op.f('ix_corporate_events_symbol'), table_name='corporate_events')
    op.drop_table('corporate_events')
