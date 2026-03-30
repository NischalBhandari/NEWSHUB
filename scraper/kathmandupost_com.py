import requests
from bs4 import BeautifulSoup
from database.db_utils import insert_news
def fetch_news():
    url = "https://kathmandupost.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    seen = set()
    articles_data = []
    unique_articles = []
    articles = soup.find_all("article", class_="article-image")

    for article in articles:
        h3 = article.find("h3")
        p = article.find("p")
        if h3 and p:
            a_tag = h3.find("a")
            if a_tag:
                title = a_tag.get_text(strip=True)
                href = a_tag.get("href")
                link = "https://kathmandupost.com" + href

                article_page = requests.get(link)
                article_soup = BeautifulSoup(article_page.text, "html.parser")
                article_body = article_soup.find("section", class_="story-section")
                content = "\n".join([p.get_text() for p in article_body.find_all("p")]) if article_body else ""
    
                description = p.get_text(strip=True)
                articles_data.append({
                    "title": title,
                    "description": description,
                    "link": link,
                    "content": content,
                    "source": "Kathmandu Post"
                })

    for item in articles_data:
        if item["link"] not in seen:
            seen.add(item["link"])
            unique_articles.append(item)
            print(item)

    articles_data = unique_articles
    for article in articles_data:
        insert_news(article)


if __name__ == "__main__":
    fetch_news()