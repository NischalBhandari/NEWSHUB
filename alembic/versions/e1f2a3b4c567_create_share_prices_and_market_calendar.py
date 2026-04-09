"""create share_prices and market_calendar tables

Revision ID: e1f2a3b4c567
Revises: d7e8f9a0b123
Create Date: 2026-04-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1f2a3b4c567'
down_revision: Union[str, Sequence[str], None] = 'd7e8f9a0b123'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'market_calendar',
        sa.Column('date',           sa.Date(),    nullable=False),
        sa.Column('is_trading_day', sa.Boolean(), nullable=False),
        sa.Column('holiday_name',   sa.Text(),    nullable=True),
        sa.Column('created_at',     sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('date'),
    )

    op.create_table(
        'share_prices',
        sa.Column('id',                sa.Integer(),  nullable=False),
        sa.Column('symbol',            sa.Text(),     nullable=False),
        sa.Column('trade_date',        sa.Date(),     nullable=False),
        sa.Column('ltp',               sa.Numeric(),  nullable=True),
        sa.Column('change_percent',    sa.Numeric(),  nullable=True),
        sa.Column('quality',           sa.Text(),     nullable=True),
        sa.Column('fundamental_score', sa.Text(),     nullable=True),
        sa.Column('valuation',         sa.Text(),     nullable=True),
        sa.Column('stars',             sa.Integer(),  nullable=True),
        sa.Column('sector',            sa.Text(),     nullable=True),
        sa.Column('created_at',        sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'trade_date', name='uq_share_price_symbol_date'),
    )


def downgrade() -> None:
    op.drop_table('share_prices')
    op.drop_table('market_calendar')
