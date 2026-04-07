import os
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine


DEFAULT_DATABASE_URL = "sqlite:///./voicebot.db"
database_url = os.getenv(
    "DATABASE_URL",
    DEFAULT_DATABASE_URL,
)
engine_kwargs: dict = {}
if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(database_url, **engine_kwargs)


# Create all database tables defined in SQLModel models.
def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


# Provide a database session for FastAPI routes.
def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
