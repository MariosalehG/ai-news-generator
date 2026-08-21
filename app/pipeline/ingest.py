# Pipeline stage 1: pulls new items from all sources (YouTube channels, OpenAI, Anthropic) and stores them in the DB
from __future__ import annotations

import json
from pathlib import Path

from app.db.repository import ArticleRepository
from app.scrapers.anthropic_news import AnthropicScraper
from app.scrapers.openai_news import OpenAINewsScraper
from app.scrapers.youtube import YouTubeScraper

YOUTUBE_CHANNELS_FILE = Path(__file__).resolve().parent.parent / "config" / "youtube_channels.json"


def load_youtube_channels() -> list[str]:
    return json.loads(YOUTUBE_CHANNELS_FILE.read_text(encoding="utf-8"))


def run(hours: int = 24) -> dict[str, dict[str, int]]:
    """Fetch everything published in the last `hours` from every source.
    New items are inserted; items whose external_id already exists are overwritten."""
    repo = ArticleRepository()
    saved = {"youtube": 0, "openai": 0, "anthropic": 0}
    updated = {"youtube": 0, "openai": 0, "anthropic": 0}

    youtube = YouTubeScraper()
    for channel_url in load_youtube_channels():
        channel_id = youtube.resolve_channel_id(channel_url)
        for video in youtube.fetch_recent_videos(channel_id, hours=hours):
            transcript = youtube.fetch_transcript(video.video_id)
            _, created = repo.upsert(
                source_type="youtube",
                source_name=video.channel_title,
                external_id=video.video_id,
                title=video.title,
                url=video.url,
                category=None,
                summary=video.summary,
                content=transcript.text if transcript else None,
                published_at=video.published,
            )
            (saved if created else updated)["youtube"] += 1

    openai_scraper = OpenAINewsScraper()
    for item in openai_scraper.list_articles(hours=hours):
        content = openai_scraper.url_to_markdown(item.url)
        _, created = repo.upsert(
            source_type="openai",
            source_name="OpenAI",
            external_id=item.guid,
            title=item.title,
            url=item.url,
            category=item.category,
            summary=item.summary,
            content=content.text if content else None,
            published_at=item.published,
        )
        (saved if created else updated)["openai"] += 1

    anthropic_scraper = AnthropicScraper()
    for item in anthropic_scraper.list_articles(hours=hours):
        content = anthropic_scraper.fetch_article_text(item.url)
        _, created = repo.upsert(
            source_type="anthropic",
            source_name=f"Anthropic {item.source}",
            external_id=item.guid,
            title=item.title,
            url=item.url,
            category=item.category,
            summary=item.summary,
            content=content.text if content else None,
            published_at=item.published,
        )
        (saved if created else updated)["anthropic"] += 1

    repo.close()
    return {"saved": saved, "updated": updated}
