# Fetches a video's transcript, by video ID, via the youtube-transcript-api library
from __future__ import annotations

from youtube_transcript_api import CouldNotRetrieveTranscript, YouTubeTranscriptApi

_api = YouTubeTranscriptApi()


def fetch_transcript(video_id: str, languages: tuple[str, ...] = ("en",)) -> str | None:
    """Return the video's transcript as plain text, or None if unavailable."""
    try:
        fetched = _api.fetch(video_id, languages=list(languages))
    except CouldNotRetrieveTranscript:
        return None
    return " ".join(snippet.text for snippet in fetched)


if __name__ == "__main__":
    video_id = "-3v_eHxKw6M"
    print(_api.fetch(video_id, languages=("en", "ar")))
    
