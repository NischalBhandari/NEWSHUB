"""merge stock and main branches

Revision ID: a1b2c3d4e5f6
Revises: 381e73d0f618, f2a3b4c5d678
Create Date: 2026-04-05 00:00:00.000000

"""
from typing import Sequence, Union

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = ('381e73d0f618', 'f2a3b4c5d678')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
