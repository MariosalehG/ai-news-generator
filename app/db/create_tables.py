# Creates all tables defined on Base.metadata (run once against a fresh database)
from app.core.database import Base, engine
from app.db import models  # noqa: F401  (import registers Article on Base.metadata)


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


if __name__ == "__main__":
    create_tables()
