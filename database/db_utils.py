from sqlalchemy.orm import sessionmaker
from database.db import engine
from models.news import News

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

        news_item = News(**filtered_article)
        session.add(news_item)
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
        news_objects = []
        for a in articles:
            filtered = {k: v for k, v in a.items() if k in allowed_keys}
            if "link" not in filtered or not filtered["link"]:
                continue
            news_objects.append(News(**filtered))

        if news_objects:
            session.bulk_save_objects(news_objects)
            session.commit()
            print(f"Inserted {len(news_objects)} articles")
    except Exception as e:
        session.rollback()
        print("Error inserting batch:", e)
    finally:
        session.close()