import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from database.db_utils import insert_news_batch

# BBC RSS feeds relevant to stock market analysis
FEEDS = {
    "BBC Business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "BBC World":    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "BBC Asia":     "https://feeds.bbci.co.uk/news/world/asia/rss.xml",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# BBC RSS uses a media namespace for thumbnails
NS = {"media": "http://search.yahoo.com/mrss/"}


def _parse_feed(feed_name: str, feed_url: str) -> list[dict]:
    response = requests.get(feed_url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    channel = root.find("channel")
    if channel is None:
        return []

    articles = []
    for item in channel.findall("item"):
        link = item.findtext("link", "").strip()
        if not link:
            continue

        title = item.findtext("title", "").strip()
        description = item.findtext("description", "").strip()

        pub_date_raw = item.findtext("pubDate", "")
        try:
            published_at = parsedate_to_datetime(pub_date_raw).astimezone(timezone.utc)
            published_at = published_at.replace(tzinfo=None)  # store as naive UTC
        except Exception:
            published_at = None

        content = _fetch_article_content(link)

        articles.append({
            "title": title,
            "link": link,
            "description": description,
            "content": content,
            "published_at": published_at,
            "source": feed_name,
        })

    return articles


def _fetch_article_content(url: str) -> str:
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return ""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        # BBC article body lives in <article> or divs with data-component="text-block"
        blocks = soup.find_all("div", attrs={"data-component": "text-block"})
        if blocks:
            return "\n".join(b.get_text(separator=" ", strip=True) for b in blocks)
        # Fallback: grab all <p> inside <article>
        article_tag = soup.find("article")
        if article_tag:
            return "\n".join(p.get_text(strip=True) for p in article_tag.find_all("p"))
        return ""
    except Exception:
        return ""


def fetch_bbc_news():
    all_articles = []
    for feed_name, feed_url in FEEDS.items():
        print(f"Fetching {feed_name}...")
        try:
            articles = _parse_feed(feed_name, feed_url)
            print(f"  Found {len(articles)} articles")
            all_articles.extend(articles)
        except Exception as e:
            print(f"  Error fetching {feed_name}: {e}")

    if all_articles:
        insert_news_batch(all_articles)
        print(f"Done. Inserted up to {len(all_articles)} articles (duplicates skipped).")


if __name__ == "__main__":
    fetch_bbc_news()
