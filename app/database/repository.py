# Simple repository for reading/writing Article rows
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.database import SessionLocal
from app.database.models import Article, Digest


class ArticleRepository:
    def __init__(self, session: Session | None = None):
        self.session = session or SessionLocal()

    def exists(self, source_type: str, external_id: str) -> bool:
        stmt = select(Article.id).where(
            Article.source_type == source_type, Article.external_id == external_id
        )
        return self.session.execute(stmt).first() is not None

    def add(self, **fields) -> Article | None:
        """Insert a new article. Returns None if one with the same source_type/external_id already exists."""
        if self.exists(fields["source_type"], fields["external_id"]):
            return None
        article = Article(**fields)
        self.session.add(article)
        self.session.commit()
        self.session.refresh(article)
        return article

    def upsert(self, **fields) -> tuple[Article, bool]:
        """Insert a new article, or overwrite the existing one with the same
        source_type/external_id. Returns (article, created)."""
        stmt = select(Article).where(
            Article.source_type == fields["source_type"], Article.external_id == fields["external_id"]
        )
        article = self.session.scalars(stmt).first()
        created = article is None
        if created:
            article = Article(**fields)
            self.session.add(article)
        else:
            for key, value in fields.items():
                setattr(article, key, value)
        self.session.commit()
        self.session.refresh(article)
        return article, created

    def list_recent(self, hours: int = 24) -> list[Article]:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = select(Article).where(Article.published_at >= since).order_by(Article.published_at.desc())
        return list(self.session.scalars(stmt))

    def list_missing_content(self) -> list[Article]:
        stmt = select(Article).where(Article.content.is_(None))
        return list(self.session.scalars(stmt))

    def set_content(self, article: Article, content: str) -> None:
        article.content = content
        self.session.commit()

    def list_without_digest(self) -> list[Article]:
        """Articles that have content but no digest entry yet."""
        digested_ids = select(Digest.article_id)
        stmt = select(Article).where(Article.content.is_not(None), Article.id.not_in(digested_ids))
        return list(self.session.scalars(stmt))

    def close(self) -> None:
        self.session.close()


class DigestRepository:
    def __init__(self, session: Session | None = None):
        self.session = session or SessionLocal()

    def exists(self, article_id: int) -> bool:
        stmt = select(Digest.id).where(Digest.article_id == article_id)
        return self.session.execute(stmt).first() is not None

    def add(self, article_id: int, url: str, title: str, summary: str) -> Digest | None:
        """Insert a new digest. Returns None if one already exists for this article."""
        if self.exists(article_id):
            return None
        digest = Digest(article_id=article_id, url=url, title=title, summary=summary)
        self.session.add(digest)
        self.session.commit()
        self.session.refresh(digest)
        return digest

    def close(self) -> None:
        self.session.close()
