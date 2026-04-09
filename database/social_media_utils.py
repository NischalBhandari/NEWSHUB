from datetime import datetime, timezone
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from database.db import engine
from models.social_media import SocialMediaPost, SocialMediaComment

Session = sessionmaker(bind=engine)

# ---------------------------------------------------------------------------
# Insert
# ---------------------------------------------------------------------------

def insert_post(post: dict) -> int | None:
    """
    Insert a single social media post. Returns the new row id, or None on failure.
    Silently skips if text is empty.
    """
    text = (post.get("text") or "").strip()
    if not text:
        return None

    session = Session()
    try:
        scraped_at = _parse_ts(post.get("scraped_at"))
        row = SocialMediaPost(
            group_name=post.get("group"),
            author=post.get("author"),
            text=text,
            reactions=post.get("reactions"),
            url=post.get("url"),
            scraped_at=scraped_at,
        )
        session.add(row)
        session.flush()   # get row.id before commit
        post_id = row.id
        session.commit()
        return post_id
    except Exception as e:
        session.rollback()
        print(f"Error inserting post: {e}")
        return None
    finally:
        session.close()


def insert_comment(comment: dict, post_id: int) -> None:
    """Insert a single comment linked to post_id."""
    text = (comment.get("text") or "").strip()
    if not text:
        return

    session = Session()
    try:
        row = SocialMediaComment(
            post_id=post_id,
            author=comment.get("author"),
            text=text,
            scraped_at=_parse_ts(comment.get("scraped_at")),
        )
        session.add(row)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error inserting comment: {e}")
    finally:
        session.close()


def insert_post_with_comments(post: dict) -> int | None:
    """
    Insert a post and all its comments in one call.
    Returns the post id or None on failure.
    """
    post_id = insert_post(post)
    if post_id is None:
        return None
    for comment in post.get("comments") or []:
        insert_comment(comment, post_id)
    return post_id


# ---------------------------------------------------------------------------
# Fetch unanalyzed (for the analysis pipeline)
# ---------------------------------------------------------------------------

def fetch_unanalyzed_posts(batch_size: int = 20) -> list[SocialMediaPost]:
    session = Session()
    try:
        stmt = select(SocialMediaPost).where(SocialMediaPost.sentiment == None).limit(batch_size)
        return session.execute(stmt).scalars().all()
    finally:
        session.close()


def fetch_unanalyzed_comments(batch_size: int = 50) -> list[SocialMediaComment]:
    session = Session()
    try:
        stmt = select(SocialMediaComment).where(SocialMediaComment.sentiment == None).limit(batch_size)
        return session.execute(stmt).scalars().all()
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Update analysis results
# ---------------------------------------------------------------------------

ALLOWED_ANALYSIS_KEYS = {
    "sentiment", "sentiment_score", "relevance_score",
    "impact_level", "market_signal", "affected_sectors",
    "entities", "keywords",
}


def update_post_analysis(post_id: int, analysis: dict) -> None:
    _update_analysis(SocialMediaPost, post_id, analysis)


def update_comment_analysis(comment_id: int, analysis: dict) -> None:
    _update_analysis(SocialMediaComment, comment_id, analysis)


def _update_analysis(model, row_id: int, analysis: dict) -> None:
    session = Session()
    try:
        row = session.get(model, row_id)
        if not row:
            return
        for key, val in analysis.items():
            if key in ALLOWED_ANALYSIS_KEYS:
                setattr(row, key, val)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error updating analysis for {model.__tablename__} id={row_id}: {e}")
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _parse_ts(value) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
