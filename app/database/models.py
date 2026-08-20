# SQLAlchemy models for scraped content (YouTube videos, OpenAI/Anthropic articles)
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.database import Base


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (UniqueConstraint("source_type", "external_id", name="uq_articles_source_external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    source_type: Mapped[str] = mapped_column(String(20))  # "youtube", "openai", "anthropic"
    source_name: Mapped[str] = mapped_column(String(200))  # channel title / "OpenAI" / "Anthropic Research"
    external_id: Mapped[str] = mapped_column(String(200))  # video_id or feed guid, unique per source_type

    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(500))
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # transcript or full article text

    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
