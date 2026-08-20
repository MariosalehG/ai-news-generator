# Stage 5: take the curator's ranked digests, limit to the top 10, and draft the email intro
# (this does not assemble or send the full email yet -- that's the next step)
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.agents.curator_agent import load_user_profile
from app.agents.email_agent import EmailAgent, top_n
from app.scripts.curate_digest import run as curate


def run(hours: int = 24) -> dict:
    ranked = curate(hours=hours)
    top = top_n(ranked)

    profile = load_user_profile()
    agent = EmailAgent()
    intro = agent.write_intro(name=profile.get("name", "there"), items=top)

    return {"intro": intro.intro, "items": top}


if __name__ == "__main__":
    result = run(hours=24)
    print(result["intro"])
    print()
    for item in result["items"]:
        print(f"[{item['score']:>3}] {item['title']} ({item['url']})")
