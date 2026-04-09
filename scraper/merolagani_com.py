import requests
from bs4 import BeautifulSoup
from datetime import datetime
from database.db_utils import insert_news_batch

BASE_URL = "https://eng.merolagani.com"

# Category pages to scrape — each maps to a NEPSE-relevant section
CATEGORY_URLS = {
    "Homepage":           f"{BASE_URL}/",
    "Latest News":        f"{BASE_URL}/NewsList.aspx",
    "Corporate":          f"{BASE_URL}/NewsList.aspx?id=17&type=latest",
    "International":      f"{BASE_URL}/NewsList.aspx?id=12&type=latest",
    "Insurance":          f"{BASE_URL}/NewsList.aspx?id=13&type=latest",
    "Opinion & Analysis": f"{BASE_URL}/NewsList.aspx?id=10&type=latest",
    "Technical Analysis": f"{BASE_URL}/NewsList.aspx?id=15&type=latest",
    "Current Affairs":    f"{BASE_URL}/NewsList.aspx?id=25&type=latest",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}


def _parse_date(text: str) -> datetime | None:
    """Parse MeroLagani date format: 'Sun, Apr 05, 2026'"""
    try:
        return datetime.strptime(text.strip(), "%a, %b %d, %Y")
    except ValueError:
        return None


def _fetch_article(url: str) -> tuple[str, datetime | None]:
    """Fetch full article content and published date from a detail page."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return "", None
        soup = BeautifulSoup(response.text, "html.parser")

        # Published date
        date_tag = soup.find("p", class_="date-topbar")
        published_at = _parse_date(date_tag.get_text()) if date_tag else None

        # Article body
        body = soup.find("div", id="ctl00_ContentPlaceHolder1_newsOverview")
        content = "\n".join(p.get_text(strip=True) for p in body.find_all("p")) if body else ""

        return content, published_at
    except Exception:
        return "", None


def _scrape_category(category_name: str, url: str) -> list[dict]:
    """Scrape all article links from a category listing page."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"  Error fetching {category_name}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    wrappers = soup.find_all("div", class_="media-news")

    articles = []
    seen_links = set()

    for wrapper in wrappers:
        # NewsList pages: title in h4.media-title > a, date in span.media-label
        # Homepage: title in a > span (no h4)
        title_tag = wrapper.find("h4", class_="media-title")
        if title_tag:
            a_tag = title_tag.find("a", href=True)
            title = a_tag.get_text(strip=True) if a_tag else ""
            # Date is available on listing page for NewsList
            label = wrapper.find("span", class_="media-label")
            listing_date = label.get_text(strip=True) if label else None
        else:
            a_tag = wrapper.find("a", href=True)
            span = a_tag.find("span") if a_tag else None
            title = span.get_text(strip=True) if span else (a_tag.get_text(strip=True) if a_tag else "")
            listing_date = None

        if not a_tag or not title:
            continue

        href = a_tag["href"].strip()
        if not href or href == "#" or "NewsDetail" not in href:
            continue

        link = href if href.startswith("http") else BASE_URL + href
        if link in seen_links:
            continue
        seen_links.add(link)

        content, published_at = _fetch_article(link)

        # Fall back to listing date if article page has no date
        if not published_at and listing_date:
            try:
                published_at = datetime.strptime(listing_date, "%b %d, %Y %I:%M %p")
            except ValueError:
                pass

        articles.append({
            "title":        title,
            "link":         link,
            "description":  "",
            "content":      content,
            "published_at": published_at,
            "source":       f"MeroLagani – {category_name}",
        })
        print(f"    Scraped: {title[:70]}")

    return articles


def fetch_merolagani_news():
    all_articles = []

    for category_name, url in CATEGORY_URLS.items():
        print(f"Fetching [{category_name}]...")
        articles = _scrape_category(category_name, url)
        print(f"  Found {len(articles)} articles")
        all_articles.extend(articles)

    if all_articles:
        insert_news_batch(all_articles)
        print(f"\nDone. Inserted up to {len(all_articles)} articles (duplicates skipped).")
    else:
        print("No articles found.")


if __name__ == "__main__":
    fetch_merolagani_news()
