# Stage 5: take the curator's ranked digests, limit to the top 10, and assemble the email digest
# (this produces the structured digest + its markdown rendering -- sending the email is the next step)
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.agents.curator_agent import load_user_profile
from app.agents.email_agent import EmailAgent, EmailArticle, EmailDigest, top_n
from app.scripts.curate_digest import run as curate


def run(hours: int = 24) -> EmailDigest:
    ranked = curate(hours=hours)
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


if __name__ == "__main__":
    digest = run(hours=24)
    print(digest.to_markdown())
