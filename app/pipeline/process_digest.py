# Pipeline stage 3: summarize articles that have content but no digest yet, via the DigestAgent
from __future__ import annotations

from app.agents.digest_agent import DigestAgent
from app.db.models import Digest
from app.db.repository import ArticleRepository, DigestRepository


def run() -> list[Digest]:
    article_repo = ArticleRepository()
    digest_repo = DigestRepository(session=article_repo.session)
    agent = DigestAgent()

    created: list[Digest] = []
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
            created.append(digest)

    article_repo.close()
    return created
