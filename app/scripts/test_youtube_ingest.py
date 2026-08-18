# Standalone smoke test: resolve channel URLs -> RSS feed -> recent videos -> transcript
from app.scrapers.youtube_rss import fetch_latest_videos, fetch_recent_videos, resolve_channel_id
from app.scrapers.youtube_transcript import fetch_transcript

CHANNEL_URLS = [
    "https://www.youtube.com/@mkbhd",
    "https://www.youtube.com/@GoogleDeepMind",
    "https://www.youtube.com/channel/UCXZCJLdBC09xxGZ6gcdrc6A",  # OpenAI
]


def main() -> None:
    for url in CHANNEL_URLS:
        print(f"\n=== {url} ===")
        channel_id = resolve_channel_id(url)
        print(f"channel_id: {channel_id}")

        all_videos = fetch_latest_videos(channel_id)
        recent = fetch_recent_videos(channel_id)
        print(f"videos in feed: {len(all_videos)} | published in last 24h: {len(recent)}")

        for v in all_videos[:3]:
            print(f"  - [{v.published.isoformat()}] {v.title} ({v.video_id})")

        if all_videos:
            video = all_videos[0]
            transcript = fetch_transcript(video.video_id)
            if transcript:
                print(f"  transcript ({len(transcript)} chars): {transcript[:200]}...")
            else:
                print("  transcript: unavailable")


if __name__ == "__main__":
    main()
