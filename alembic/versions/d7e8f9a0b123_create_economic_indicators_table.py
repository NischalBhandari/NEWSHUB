"""create economic_indicators table

Revision ID: d7e8f9a0b123
Revises: c5d6e7f8a912
Create Date: 2026-04-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7e8f9a0b123'
down_revision: Union[str, Sequence[str], None] = 'c5d6e7f8a912'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'economic_indicators',
        sa.Column('id',        sa.Integer(),  nullable=False),
        sa.Column('indicator', sa.Text(),     nullable=False),
        sa.Column('category',  sa.Text(),     nullable=True),
        sa.Column('value',     sa.Numeric(),  nullable=True),
        sa.Column('previous',  sa.Numeric(),  nullable=True),
        sa.Column('highest',   sa.Numeric(),  nullable=True),
        sa.Column('lowest',    sa.Numeric(),  nullable=True),
        sa.Column('unit',      sa.Text(),     nullable=True),
        sa.Column('reference', sa.Text(),     nullable=True),
        sa.Column('year',      sa.Integer(),  nullable=True),
        sa.Column('month',     sa.Integer(),  nullable=True),
        sa.Column('country',   sa.Text(),     nullable=True),
        sa.Column('source',    sa.Text(),     nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('indicator', 'year', 'month', 'country',
                            name='uq_indicator_period_country'),
    )


def downgrade() -> None:
    op.drop_table('economic_indicators')
