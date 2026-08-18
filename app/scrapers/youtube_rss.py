# Fetches latest videos for a YouTube channel via its RSS feed (feedparser)
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import feedparser
import requests

FEED_URL = "https://www.youtube.com/feeds/videos.xml"
CHANNEL_ID_RE = re.compile(r"UC[\w-]{22}")
HEADERS = {"User-Agent": "Mozilla/5.0"}


@dataclass
class VideoEntry:
    video_id: str
    title: str
    url: str
    published: datetime
    channel_id: str
    channel_title: str


def resolve_channel_id(channel_url: str) -> str:
    """Resolve any YouTube channel URL (/channel/UC…, @handle, /c/…, /user/…) to its UC… channel ID."""
    match = CHANNEL_ID_RE.search(channel_url)
    if match and "/channel/" in channel_url:
        return match.group(0)

    resp = requests.get(channel_url, timeout=10, headers=HEADERS)
    resp.raise_for_status()

    # Try the canonical/RSS <link> tags first: unlike the embedded JSON blobs (which
    # reference many unrelated channelIds for related/recommended channels), these
    # reliably point at the page's own channel.
    for pattern in (
        r'<link rel="canonical" href="https://www\.youtube\.com/channel/(UC[\w-]{22})"',
        r'<link rel="alternate" type="application/rss\+xml"[^>]*channel_id=(UC[\w-]{22})"',
        r'<meta itemprop="channelId" content="(UC[\w-]{22})"',
        r'"externalId":"(UC[\w-]{22})"',
    ):
        found = re.search(pattern, resp.text)
        if found:
            return found.group(1)

    raise ValueError(f"Could not resolve channel ID from {channel_url}")


def channel_feed_url(channel_id: str) -> str:
    return f"{FEED_URL}?channel_id={channel_id}"


def fetch_latest_videos(channel_id: str, retries: int = 3) -> list[VideoEntry]:
    """Fetch all entries currently in the channel's RSS feed (YouTube caps this at ~15).

    YouTube's feed endpoint intermittently 404s known-good channels under rate limiting;
    a short backoff-and-retry clears it.
    """
    last_status = None
    for attempt in range(retries):
        resp = requests.get(channel_feed_url(channel_id), timeout=100, headers=HEADERS)
        if resp.status_code == 200:
            break
        last_status = resp.status_code
        time.sleep(2**attempt)
    else:
        raise RuntimeError(
            f"Failed to fetch feed for channel {channel_id} after {retries} attempts "
            f"(last status: {last_status})"
        )

    feed = feedparser.parse(resp.content)

    videos = []
    for entry in feed.entries:
        videos.append(
            VideoEntry(
                video_id=entry.yt_videoid,
                title=entry.title,
                url=entry.link,
                published=datetime(*entry.published_parsed[:6], tzinfo=timezone.utc),
                channel_id=channel_id,
                channel_title=getattr(feed.feed, "title", ""),
            )
        )
    return videos


def fetch_recent_videos(channel_id: str, hours: int | None = None) -> list[VideoEntry]:
    """Fetch videos published since the given time (default: the last 24 hours)."""
    if hours is None:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
    else:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
    return [v for v in fetch_latest_videos(channel_id) if v.published >= since]


