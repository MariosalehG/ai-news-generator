# Runner: pulls new items from all sources (YouTube channels, OpenAI, Anthropic) within a time window
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.scrapers.anthropic_news import AnthropicScraper
from app.scrapers.openai_news import OpenAINewsScraper
from app.scrapers.youtube import YouTubeScraper

YOUTUBE_CHANNELS_FILE = Path(__file__).resolve().parent.parent / "config" / "youtube_channels.json"


def load_youtube_channels() -> list[str]:
    return json.loads(YOUTUBE_CHANNELS_FILE.read_text(encoding="utf-8"))


def run(hours: int = 24) -> dict[str, list[dict]]:
    """Fetch everything published in the last `hours` from every source."""
    results: dict[str, list[dict]] = {"youtube": [], "openai": [], "anthropic": []}

    youtube = YouTubeScraper()
    for channel_url in load_youtube_channels():
        channel_id = youtube.resolve_channel_id(channel_url)
        for video in youtube.fetch_recent_videos(channel_id, hours=hours):
            results["youtube"].append(
                {"video": video, "transcript": youtube.fetch_transcript(video.video_id)}
            )

    openai_scraper = OpenAINewsScraper()
    for article in openai_scraper.list_articles(hours=hours):
        results["openai"].append(
            {"article": article, "content": openai_scraper.fetch_article_text(article.url)}
        )

    anthropic_scraper = AnthropicScraper()
    for article in anthropic_scraper.list_articles(hours=hours):
        results["anthropic"].append(
            {"article": article, "content": anthropic_scraper.fetch_article_text(article.url)}
        )

    return results


if __name__ == "__main__":
    results = run(hours=72)
    for source, items in results.items():
        print(f"\n=== {source}: {len(items)} new item(s) ===")
        for item in items:
            entry = item.get("video") or item.get("article")
            print(f"- [{entry.published.isoformat()}] {entry.title} ({entry.url})")
