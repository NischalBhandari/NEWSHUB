"""create social_media_posts and social_media_comments tables

Revision ID: b1c2d3e4f567
Revises: a1b2c3d4e5f6
Create Date: 2026-04-07 00:00:00.000000
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = 'b1c2d3e4f567'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ANALYSIS_COLS = [
    sa.Column("sentiment",        sa.Text),
    sa.Column("sentiment_score",  sa.Numeric(4, 3)),
    sa.Column("relevance_score",  sa.Numeric(4, 3)),
    sa.Column("impact_level",     sa.Text),
    sa.Column("market_signal",    sa.Text),
    sa.Column("affected_sectors", sa.Text),
    sa.Column("entities",         sa.Text),
    sa.Column("keywords",         sa.Text),
]


def upgrade() -> None:
    op.create_table(
        "social_media_posts",
        sa.Column("id",         sa.Integer, primary_key=True),
        sa.Column("group_name", sa.Text),
        sa.Column("author",     sa.Text),
        sa.Column("text",       sa.Text, nullable=False),
        sa.Column("reactions",  sa.Text),
        sa.Column("url",        sa.Text),
        sa.Column("scraped_at", sa.TIMESTAMP),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        *ANALYSIS_COLS,
    )

    op.create_table(
        "social_media_comments",
        sa.Column("id",      sa.Integer, primary_key=True),
        sa.Column("post_id", sa.Integer, sa.ForeignKey("social_media_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author",     sa.Text),
        sa.Column("text",       sa.Text, nullable=False),
        sa.Column("scraped_at", sa.TIMESTAMP),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        *ANALYSIS_COLS,
    )

    op.create_index("ix_social_media_comments_post_id", "social_media_comments", ["post_id"])


def downgrade() -> None:
    op.drop_index("ix_social_media_comments_post_id", table_name="social_media_comments")
    op.drop_table("social_media_comments")
    op.drop_table("social_media_posts")
