"""expand share_prices with full financial columns

Revision ID: f2a3b4c5d678
Revises: e1f2a3b4c567
Create Date: 2026-04-05 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f2a3b4c5d678'
down_revision: Union[str, Sequence[str], None] = 'e1f2a3b4c567'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename misnamed columns from the original scraper mapping
    op.alter_column('share_prices', 'fundamental_score', new_column_name='graham_distance')
    op.alter_column('share_prices', 'valuation',         new_column_name='pe_vs_sector')

    # Add valuation ratio columns
    op.add_column('share_prices', sa.Column('pe',             sa.Numeric(), nullable=True))
    op.add_column('share_prices', sa.Column('pb',             sa.Numeric(), nullable=True))
    op.add_column('share_prices', sa.Column('roe',            sa.Numeric(), nullable=True))
    op.add_column('share_prices', sa.Column('roa',            sa.Numeric(), nullable=True))
    op.add_column('share_prices', sa.Column('peg',            sa.Numeric(), nullable=True))
    op.add_column('share_prices', sa.Column('dividend_yield', sa.Numeric(), nullable=True))
    op.add_column('share_prices', sa.Column('payout_ratio',   sa.Numeric(), nullable=True))

    # Add vs-sector comparison columns
    op.add_column('share_prices', sa.Column('pb_vs_sector',             sa.Text(), nullable=True))
    op.add_column('share_prices', sa.Column('peg_vs_sector',            sa.Text(), nullable=True))
    op.add_column('share_prices', sa.Column('dividend_yield_vs_sector', sa.Text(), nullable=True))
    op.add_column('share_prices', sa.Column('roe_vs_sector',            sa.Text(), nullable=True))
    op.add_column('share_prices', sa.Column('yoy_growth_vs_sector',     sa.Text(), nullable=True))
    op.add_column('share_prices', sa.Column('qoq_growth_vs_sector',     sa.Text(), nullable=True))
    op.add_column('share_prices', sa.Column('roa_vs_sector',            sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('share_prices', 'roa_vs_sector')
    op.drop_column('share_prices', 'qoq_growth_vs_sector')
    op.drop_column('share_prices', 'yoy_growth_vs_sector')
    op.drop_column('share_prices', 'roe_vs_sector')
    op.drop_column('share_prices', 'dividend_yield_vs_sector')
    op.drop_column('share_prices', 'peg_vs_sector')
    op.drop_column('share_prices', 'pb_vs_sector')
    op.drop_column('share_prices', 'payout_ratio')
    op.drop_column('share_prices', 'dividend_yield')
    op.drop_column('share_prices', 'peg')
    op.drop_column('share_prices', 'roa')
    op.drop_column('share_prices', 'roe')
    op.drop_column('share_prices', 'pb')
    op.drop_column('share_prices', 'pe')
    op.alter_column('share_prices', 'pe_vs_sector',    new_column_name='valuation')
    op.alter_column('share_prices', 'graham_distance', new_column_name='fundamental_score')
