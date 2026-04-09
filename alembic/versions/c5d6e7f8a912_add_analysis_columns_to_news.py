"""add analysis columns to news

Revision ID: c5d6e7f8a912
Revises: 394c8afef412
Create Date: 2026-04-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5d6e7f8a912'
down_revision: Union[str, Sequence[str], None] = '394c8afef412'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('news', sa.Column('sentiment', sa.Text(), nullable=True))
    op.add_column('news', sa.Column('sentiment_score', sa.Numeric(4, 3), nullable=True))
    op.add_column('news', sa.Column('relevance_score', sa.Numeric(4, 3), nullable=True))
    op.add_column('news', sa.Column('impact_level', sa.Text(), nullable=True))
    op.add_column('news', sa.Column('market_signal', sa.Text(), nullable=True))
    op.add_column('news', sa.Column('affected_sectors', sa.Text(), nullable=True))
    op.add_column('news', sa.Column('entities', sa.Text(), nullable=True))
    op.add_column('news', sa.Column('keywords', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('news', 'keywords')
    op.drop_column('news', 'entities')
    op.drop_column('news', 'affected_sectors')
    op.drop_column('news', 'market_signal')
    op.drop_column('news', 'impact_level')
    op.drop_column('news', 'relevance_score')
    op.drop_column('news', 'sentiment_score')
    op.drop_column('news', 'sentiment')
