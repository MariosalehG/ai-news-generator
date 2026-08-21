# Pipeline stage 4: rank the day's digests against the user profile
from __future__ import annotations

from app.agents.curator_agent import CuratorAgent
from app.db.models import Digest
from app.db.repository import DigestRepository


def run(hours: int = 24, digests: list[Digest] | None = None) -> list[dict]:
    """Rank the given digests. If none are passed in, fetch the last `hours` from the DB."""
    if digests is None:
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
            "summary": by_id[r.digest_id].summary,
            "url": by_id[r.digest_id].url,
        }
        for r in rankings
        if r.digest_id in by_id
    ]
