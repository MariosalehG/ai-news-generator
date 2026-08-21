# SQLAlchemy engine, sessionmaker, and declarative Base shared by all models
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url)
# expire_on_commit=False: ORM objects stay readable after commit even once their session is
# closed elsewhere (e.g. returned across module boundaries in the daily pipeline), instead of
# raising DetachedInstanceError on the next attribute access.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
