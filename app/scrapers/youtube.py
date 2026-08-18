# YouTube scraper: resolves channels, fetches recent videos via RSS, and fetches transcripts
from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests
from pydantic import BaseModel
from youtube_transcript_api import CouldNotRetrieveTranscript, YouTubeTranscriptApi

FEED_URL = "https://www.youtube.com/feeds/videos.xml"
CHANNEL_ID_RE = re.compile(r"UC[\w-]{22}")
HEADERS = {"User-Agent": "Mozilla/5.0"}


class ChannelVideo(BaseModel):
    video_id: str
    title: str
    url: str
    published: datetime
    channel_id: str
    channel_title: str


class Transcript(BaseModel):
    text: str


class YouTubeScraper:
    def __init__(self, transcript_languages: tuple[str, ...] = ("en",)):
        self.transcript_languages = transcript_languages
        self._transcript_api = YouTubeTranscriptApi()

    def resolve_channel_id(self, channel_url: str) -> str:
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

    def extract_video_id(self, video_url: str) -> str:
        """Extract the video ID from a YouTube URL."""
        match = re.search(r"(?:v=|/)([a-zA-Z0-9_-]{11})", video_url)
        if match:
            return match.group(1)
        raise ValueError(f"Could not extract video ID from {video_url}")

    def channel_feed_url(self, channel_id: str) -> str:
        return f"{FEED_URL}?channel_id={channel_id}"

    def fetch_latest_videos(self, channel_id: str, retries: int = 3) -> list[ChannelVideo]:
        """Fetch all entries currently in the channel's RSS feed (YouTube caps this at ~15).

        YouTube's feed endpoint intermittently 404s known-good channels under rate limiting;
        a short backoff-and-retry clears it.
        """
        last_status = None
        for attempt in range(retries):
            resp = requests.get(self.channel_feed_url(channel_id), timeout=10, headers=HEADERS)
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
                ChannelVideo(
                    video_id=entry.yt_videoid,
                    title=entry.title,
                    url=entry.link,
                    published=datetime(*entry.published_parsed[:6], tzinfo=timezone.utc),
                    channel_id=channel_id,
                    channel_title=getattr(feed.feed, "title", ""),
                )
            )
        return videos

    def fetch_recent_videos(self, channel_id: str, hours: int = 24) -> list[ChannelVideo]:
        """Fetch videos published within the last `hours` (default: 24)."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [v for v in self.fetch_latest_videos(channel_id) if v.published >= since]

    def fetch_transcript(self, video_id: str) -> Transcript | None:
        """Return the video's transcript, or None if unavailable."""
        try:
            fetched = self._transcript_api.fetch(video_id, languages=list(self.transcript_languages))
        except CouldNotRetrieveTranscript:
            return None
        return Transcript(text=" ".join(snippet.text for snippet in fetched))


if __name__ == "__main__":
    scraper = YouTubeScraper(transcript_languages=("ar",))
    channel_id = scraper.resolve_channel_id("https://www.youtube.com/@Asateer-ٔ-m4r")
    print(f"Channel ID: {channel_id}")
    videos = scraper.fetch_recent_videos(channel_id, hours=24)
    for video in videos:
        print(f"{video.published.isoformat()} - {video.title} ({video.url}) {video.video_id}")
        transcript = scraper.fetch_transcript(video_id=video.video_id)
        if transcript:
            print(f"Transcript: {transcript.text[:100]}...")
        else:
            print("Transcript: Not available")
