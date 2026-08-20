# Curator agent: ranks the last day's digests by relevance to a user profile,
# using the OpenAI Responses API with structured outputs (same setup as DigestAgent).
from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel

from app.core.config import settings

MODEL = "gpt-4.1-mini"

USER_PROFILE_FILE = Path(__file__).resolve().parents[1] / "config" / "user_profile.json"

SYSTEM_PROMPT = (
    "You are a news curator building a personalized daily AI news digest. You will be given a "
    "user profile (their role, background, and interests) and a list of candidate digest items "
    "from the last 24 hours, each with an id, title, and summary. Score every item from 0 to 100 "
    "for how relevant and interesting it is specifically to this user, based on their stated "
    "interests and background -- not on generic importance. Give a one-sentence reason for each "
    "score. You must return exactly one ranking entry per item given, using the same digest_id."
)


class RankedDigest(BaseModel):
    digest_id: int
    score: int  # 0-100, relevance to the user's profile
    reason: str


class CurationResult(BaseModel):
    rankings: list[RankedDigest]


def load_user_profile() -> dict:
    return json.loads(USER_PROFILE_FILE.read_text(encoding="utf-8"))


class CuratorAgent:
    def __init__(self, model: str = MODEL):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model

    def rank(self, items: list[dict], profile: dict | None = None) -> list[RankedDigest]:
        """items: list of {"digest_id": int, "title": str, "summary": str}."""
        profile = profile if profile is not None else load_user_profile()

        user_content = (
            f"User profile:\n{json.dumps(profile, indent=2)}\n\n"
            f"Candidate items:\n{json.dumps(items, indent=2)}"
        )
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            text_format=CurationResult,
        )
        rankings = response.output_parsed.rankings
        rankings.sort(key=lambda r: r.score, reverse=True)
        return rankings
