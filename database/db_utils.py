from database import get_connection

def insert_news(article):
    conn  = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO news (title, link, description, content, published_at, source)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (link) DO NOTHING;
            """, (
                article.get("title"),
                article.get("link"),
                article.get("description"),
                article.get("content"),
                article.get("published_at"),
                article.get("source")
            ))
        conn.commit()
    except Exception as e:
        print("Error inserting article:", e)
    finally:
        conn.close()

def insert_news_batch(articles):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            args_str = ",".join(
                cur.mogrify("(%s,%s,%s,%s,%s,%s)", (
                    a.get("title"),
                    a.get("link"),
                    a.get("description"),
                    a.get("content"),
                    a.get("published_at"),
                    a.get("source")
                )).decode("utf-8") for a in articles
            )
            cur.execute(f"""
                INSERT INTO news (title, link, description, content, published_at, source)
                VALUES {args_str}
                ON CONFLICT (link) DO NOTHING;
            """)
        conn.commit()
    finally:
        conn.close()