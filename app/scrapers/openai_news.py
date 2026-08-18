# OpenAI news scraper: lists latest articles via RSS and fetches article body text
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import feedparser
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
from docling.document_converter import DocumentConverter

RSS_URL = "https://openai.com/news/rss.xml"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
}


class NewsArticle(BaseModel):
    title: str
    url: str
    category: str
    summary: str
    published: datetime
    guid: str


class ArticleContent(BaseModel):
    text: str


class OpenAINewsScraper:
    def __init__(self):
            self.converter = DocumentConverter()

    def list_articles(self, hours: int | None = None) -> list[NewsArticle]:
        """Fetch articles from the RSS feed, optionally filtered to those published in the last `hours`."""
        resp = requests.get(RSS_URL, timeout=10, headers=HEADERS)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        articles = [
            NewsArticle(
                title=entry.title,
                url=entry.link,
                category=(entry.get("tags") or [{}])[0].get("term", ""),
                summary=entry.get("summary", ""),
                published=datetime(*entry.published_parsed[:6], tzinfo=timezone.utc),
                guid=entry.get("guid", entry.link)
            )
            for entry in feed.entries
        ]

        if hours is not None:
            since = datetime.now(timezone.utc) - timedelta(hours=hours)
            articles = [a for a in articles if a.published >= since]

        return articles

    def fetch_article_text(self, url: str) -> ArticleContent:
        """Fetch and extract an article's body text (not available via RSS)."""
        resp = requests.get(url, timeout=10, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")

        article = soup.find("article")
        if article is None:
            raise ValueError(f"No <article> found at {url}")

        # The same <article> element also wraps a trailing "related articles" section;
        # those <p> meta blocks contain a <time> child, body paragraphs never do.
        paragraphs = [p for p in article.find_all("p") if not p.find("time")]
        text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        return ArticleContent(text=text)

    def url_to_markdown(self, url: str) -> ArticleContent | None:
        try:
            result = self.converter.convert(url)
            return ArticleContent(text = result.document.export_to_markdown())
        except Exception as e:
            print(f"Error converting {url} to markdown: {e}")
            return None

if __name__ == "__main__":
    scraper = OpenAINewsScraper()
    articles = scraper.list_articles(hours=48)
    for article in articles:
        print(f"{article.published.isoformat()} [{article.category}] {article.title} ({article.url}), published: {article.published}")
    print(f"Summary: {scraper.url_to_markdown(articles[0].url)}")
