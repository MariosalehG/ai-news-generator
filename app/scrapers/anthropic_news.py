# Anthropic scraper: combines the news, research, and engineering RSS feeds and fetches article text
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import feedparser
import requests
from docling.document_converter import DocumentConverter
from pydantic import BaseModel

FEEDS = {
    "news": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
    "research": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
    "engineering": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
}


class AnthropicArticle(BaseModel):
    title: str
    url: str
    category: str
    summary: str
    published: datetime
    guid: str
    source: str


class ArticleContent(BaseModel):
    text: str


class AnthropicScraper:
    def __init__(self):
        self.converter = DocumentConverter()

    def list_articles(self, hours: int | None = None) -> list[AnthropicArticle]:
        """Fetch articles from all three feeds, optionally filtered to those published in the last `hours`."""
        articles = []
        for source, feed_url in FEEDS.items():
            resp = requests.get(feed_url, timeout=10)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
            for entry in feed.entries:
                articles.append(
                    AnthropicArticle(
                        title=entry.title,
                        url=entry.link,
                        category=(entry.get("tags") or [{}])[0].get("term", ""),
                        summary=entry.get("summary", ""),
                        published=datetime(*entry.published_parsed[:6], tzinfo=timezone.utc),
                        guid=entry.get("guid", entry.link),
                        source=source,
                    )
                )

        articles.sort(key=lambda a: a.published, reverse=True)

        if hours is not None:
            since = datetime.now(timezone.utc) - timedelta(hours=hours)
            articles = [a for a in articles if a.published >= since]

        return articles

    def fetch_article_text(self, url: str) -> ArticleContent | None:
        """Fetch and convert an article page to plain markdown text."""
        try:
            result = self.converter.convert(url)
            return ArticleContent(text=result.document.export_to_markdown())
        except Exception as e:
            print(f"Error converting {url} to markdown: {e}")
            return None


if __name__ == "__main__":
    scraper = AnthropicScraper()
    articles = scraper.list_articles(hours=1000)
    for article in articles:
        print(f"[{article.source}] {article.published.isoformat()} {article.title} ({article.url})")

    if articles:
        content = scraper.fetch_article_text(articles[0].url)
        if content:
            print(f"\nFirst article text ({len(content.text)} chars):\n{content.text[:300]}...")
