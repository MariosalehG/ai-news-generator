# Stage 3: summarize articles that have content but no digest yet, via the DigestAgent
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.agents.digest_agent import DigestAgent
from app.database.repository import ArticleRepository, DigestRepository


def run() -> int:
    article_repo = ArticleRepository()
    digest_repo = DigestRepository(session=article_repo.session)
    agent = DigestAgent()

    created = 0
    for article in article_repo.list_without_digest():
        try:
            result = agent.summarize(article.title, article.content)
        except Exception as e:
            print(f"Error summarizing article {article.id} ({article.url}): {e}")
            continue

        digest = digest_repo.add(
            article_id=article.id,
            url=article.url,
            title=result.title,
            summary=result.summary,
        )
        if digest:
            created += 1

    article_repo.close()
    return created


if __name__ == "__main__":
    created = run()
    print(f"{created} digest(s) created")
