from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert
from database.db import engine
from models.news import News
from sqlalchemy import select, delete, or_

Session = sessionmaker(bind=engine)

def insert_news(article):
    session = Session()
    try:
        # Only include fields that exist in the model
        allowed_keys = {"title", "link", "description", "content", "published_at", "source"}
        filtered_article = {k: v for k, v in article.items() if k in allowed_keys}

        # Required field check
        if "link" not in filtered_article or not filtered_article["link"]:
            print("Skipping article with no link")
            return

        stmt = pg_insert(News).values([filtered_article]).on_conflict_do_nothing(index_elements=["link"])
        session.execute(stmt)
        session.commit()
        print(f"Inserted: {filtered_article.get('title')}")
    except Exception as e:
        session.rollback()
        print(f"Error inserting article '{article.get('title')}': {e}")
    finally:
        session.close()

def insert_news_batch(articles):
    if not articles:
        return

    session = Session()
    try:
        allowed_keys = {"title", "link", "description", "content", "published_at", "source"}
        rows = []
        for a in articles:
            filtered = {k: v for k, v in a.items() if k in allowed_keys}
            if filtered.get("link"):
                rows.append(filtered)

        if rows:
            stmt = pg_insert(News).values(rows).on_conflict_do_nothing(index_elements=["link"])
            session.execute(stmt)
            session.commit()
            print(f"Inserted batch (duplicates ignored)")
    except Exception as e:
        session.rollback()
        print("Error inserting batch:", e)
    finally:
        session.close()


def delete_empty_news():
    """Delete news rows that have neither content nor description."""
    session = Session()
    try:
        stmt = delete(News).where(
            or_(News.content == None, News.content == ""),
            or_(News.description == None, News.description == ""),
        )
        result = session.execute(stmt)
        session.commit()
        print(f"Deleted {result.rowcount} empty news rows.")
        return result.rowcount
    except Exception as e:
        session.rollback()
        print(f"Error deleting empty news: {e}")
        return 0
    finally:
        session.close()


def fetch_unanalyzed_news(batch_size: int = 20) -> list[News]:
    """Return news rows where sentiment has not been filled in yet."""
    session = Session()
    try:
        stmt = select(News).where(News.sentiment == None).limit(batch_size)
        return session.execute(stmt).scalars().all()
    finally:
        session.close()


def update_news_analysis(news_id: int, analysis: dict):
    """Write analysis fields back to a single news row by id."""
    allowed_keys = {
        "sentiment", "sentiment_score", "relevance_score",
        "impact_level", "market_signal", "affected_sectors",
        "entities", "keywords",
    }
    session = Session()
    try:
        row = session.get(News, news_id)
        if not row:
            return
        for key, val in analysis.items():
            if key in allowed_keys:
                setattr(row, key, val)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error updating analysis for news id={news_id}: {e}")
    finally:
        session.close()