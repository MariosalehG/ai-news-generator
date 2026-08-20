# Stage 4: rank the last day's digests against the user profile
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.agents.curator_agent import CuratorAgent
from app.database.repository import DigestRepository


def run(hours: int = 24) -> list[dict]:
    repo = DigestRepository()
    digests = repo.list_recent(hours=hours)
    repo.close()

    if not digests:
        return []

    by_id = {d.id: d for d in digests}
    items = [{"digest_id": d.id, "title": d.title, "summary": d.summary} for d in digests]

    agent = CuratorAgent()
    rankings = agent.rank(items)

    return [
        {
            "digest_id": r.digest_id,
            "score": r.score,
            "reason": r.reason,
            "title": by_id[r.digest_id].title,
            "url": by_id[r.digest_id].url,
        }
        for r in rankings
        if r.digest_id in by_id
    ]


if __name__ == "__main__":
    ranked = run(hours=24)
    for item in ranked:
        print(f"[{item['score']:>3}] {item['title']} ({item['url']})")
        print(f"      {item['reason']}")
