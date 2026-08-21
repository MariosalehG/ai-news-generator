# Pipeline stage 2: backfill full content (transcripts / article text) for DB rows that don't have it yet
from __future__ import annotations

from app.db.repository import ArticleRepository
from app.scrapers.anthropic_news import AnthropicScraper
from app.scrapers.openai_news import OpenAINewsScraper
from app.scrapers.youtube import YouTubeScraper


def run() -> dict[str, int]:
    """Find articles with no content yet and fetch it (video transcript or article text)."""
    repo = ArticleRepository()
    filled = {"youtube": 0, "openai": 0, "anthropic": 0}

    youtube = YouTubeScraper()
    openai_scraper = OpenAINewsScraper()
    anthropic_scraper = AnthropicScraper()

    for article in repo.list_missing_content():
        if article.source_type == "youtube":
            transcript = youtube.fetch_transcript(article.external_id)
            content = transcript.text if transcript else None
        elif article.source_type == "openai":
            result = openai_scraper.fetch_article_text(article.url)
            content = result.text if result else None
        elif article.source_type == "anthropic":
            result = anthropic_scraper.fetch_article_text(article.url)
            content = result.text if result else None
        else:
            continue

        if content:
            repo.set_content(article, content)
            filled[article.source_type] += 1

    repo.close()
    return filled
