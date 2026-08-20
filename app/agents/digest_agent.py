# Digest agent: turns one Article's full text/transcript into a short title + summary
# via the OpenAI Responses API, using structured outputs (text_format).
from __future__ import annotations

from openai import OpenAI
from pydantic import BaseModel

from app.core.config import settings

MODEL = "gpt-4.1-mini"

SYSTEM_PROMPT = (
    "You are a news digest editor for an AI industry newsletter. You will be given the title "
    "and full text (article body or video transcript) of one item from OpenAI, Anthropic, or a "
    "YouTube AI channel. Write a concise, factual digest entry for it: a short title (rewrite the "
    "original only if it's unclear out of context) and a 2-3 sentence summary of the key news or "
    "takeaway. Stick to what's in the source text; do not add outside information or opinions."
)


class DigestSummary(BaseModel):
    title: str
    summary: str


class DigestAgent:
    def __init__(self, model: str = MODEL):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model

    def summarize(self, title: str, content: str) -> DigestSummary:
        response = self.client.responses.parse(
            model=self.model,
            temperature=0.7,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Title: {title}\n\nContent:\n{content}"},
            ],
            text_format=DigestSummary,
        )
        return response.output_parsed
