# Creates all tables defined on Base.metadata (run once against a fresh database)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.database import Base, engine
from app.database import models  # noqa: F401  (import registers Article on Base.metadata)


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


if __name__ == "__main__":
    create_tables()
