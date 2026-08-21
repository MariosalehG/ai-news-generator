# Pipeline stage 5: take the curator's ranked digests, limit to the top 10, and assemble the email digest
from __future__ import annotations

from datetime import datetime

from app.agents.curator_agent import load_user_profile
from app.agents.email_agent import EmailAgent, EmailArticle, EmailDigest, top_n
from app.db.models import Digest
from app.pipeline.curate import run as curate


def run(hours: int = 24, digests: list[Digest] | None = None) -> EmailDigest:
    ranked = curate(hours=hours, digests=digests)
    top = top_n(ranked)

    profile = load_user_profile()
    name = profile.get("name", "there")

    agent = EmailAgent()
    intro = agent.write_intro(name=name, items=top)

    articles = [
        EmailArticle(
            rank=i + 1,
            title=item["title"],
            summary=item["summary"],
            url=item["url"],
            score=item["score"],
        )
        for i, item in enumerate(top)
    ]

    return EmailDigest(
        recipient_name=name,
        date=datetime.now().date(),
        greeting=intro.intro,
        articles=articles,
        total_ranked=len(ranked),
        top_n=len(top),
    )
