# Email agent: writes the intro blurb for the daily digest email, from the top-ranked digest items
# (full email assembly/sending is a later step -- this agent only produces the intro text).
from __future__ import annotations

from datetime import date as date_type
from datetime import datetime

from openai import OpenAI
from pydantic import BaseModel

from app.core.config import settings

MODEL = "gpt-4.1-mini"

TOP_N = 10

SYSTEM_PROMPT = """
You write the introduction for a personalized daily AI news email digest.

You will receive:

* The recipient's name
* Today's date
* The titles of today's top-ranked AI news items

Your goal is to produce a concise, engaging 2-3 sentence introduction that feels like a smart
editor has selected the most interesting AI developments for the reader. The ranked items
themselves are rendered separately below your introduction -- you only write the intro.

The introduction should:

* Greet the recipient naturally by name.
* Mention today's date.
* Give an engaging editorial overview of what is happening across today's AI landscape.
* Focus on the most interesting theme, development, or tension connecting the stories.
* Explain why today's developments are worth paying attention to.
* Avoid generic phrases such as "today's digest highlights," "latest breakthroughs," "shaping
  the future of AI," or "AI is rapidly evolving."
* Do not list individual stories -- that's handled separately.

Where appropriate, emphasize themes such as:

* AI moving from experimentation into real-world production
* major productivity gains
* advances in coding and software development
* scientific and industrial applications
* open-source AI
* AI infrastructure
* cybersecurity and AI safety
* regulation, governance, and policy
* competition between major AI companies

Do not force these themes if they are not present in the day's stories.

Make the intro smart and editorial rather than robotic, concise but interesting, energetic
without being sensationalist, and varied from day to day. Return only the introduction text.
"""


class EmailIntro(BaseModel):
    intro: str


class EmailArticle(BaseModel):
    rank: int
    title: str
    summary: str
    url: str
    score: int


class EmailDigest(BaseModel):
    recipient_name: str
    date: date_type
    greeting: str
    articles: list[EmailArticle]
    total_ranked: int
    top_n: int

    def to_markdown(self) -> str:
        """Render as markdown: the greeting, then one section (header + summary + link) per article."""
        parts = [self.greeting, ""]
        for article in self.articles:
            parts.append(f"## {article.rank}. {article.title}")
            parts.append("")
            parts.append(article.summary)
            parts.append("")
            parts.append(f"[Read more]({article.url})")
            parts.append("")
        return "\n".join(parts).strip()

    def to_html(self) -> str:
        """Render as a minimal HTML email: small headings per article, bold links, italic score line."""
        parts = [f"<p>{self.greeting}</p>"]
        for article in self.articles:
            parts.append(f"<h4>{article.rank}. {article.title}</h4>")
            parts.append(f"<p>{article.summary}</p>")
            parts.append(f"<p><i>Relevance: {article.score}/100</i></p>")
            parts.append(f'<p><b><a href="{article.url}">Read more &rarr;</a></b></p>')
        body = "\n".join(parts)
        return f"<html><body>{body}</body></html>"


def top_n(ranked_items: list[dict], n: int = TOP_N) -> list[dict]:
    """Take the curator agent's score-sorted output and limit it to the top `n`."""
    return ranked_items[:n]


class EmailAgent:
    def __init__(self, model: str = MODEL):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model

    def write_intro(self, name: str, items: list[dict], digest_date: date_type | None = None) -> EmailIntro:
        """items: the top-ranked digest dicts (each with at least a "title"), already limited to top N."""
        digest_date = digest_date or datetime.now().date()

        user_content = (
            f"Recipient name: {name}\n"
            f"Date: {digest_date.strftime('%B %d, %Y')}\n\n"
            "Today's top items:\n" + "\n".join(f"- {item['title']}" for item in items)
        )
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            text_format=EmailIntro,
        )
        return response.output_parsed
