"""SQLAlchemy engine, declarative Base and a lightweight connectivity check."""

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all future models.

    Milestone 1 intentionally declares no tables; Check/CheckResult come later.
    """


def create_db_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine for the given URL."""
    # SQLite guards connections against cross-thread use by default, but FastAPI
    # runs sync endpoints in a worker thread pool and the pool reuses connections
    # across those threads.
    connect_args = (
        {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    )
    return create_engine(database_url, connect_args=connect_args)


class Database:
    """Owns the engine and provides the cheapest possible liveness probe."""

    def __init__(self, database_url: str) -> None:
        self.engine = create_db_engine(database_url)

    def ping(self) -> None:
        """Run `SELECT 1` to prove the database is reachable.

        Touches no tables, so it works on a brand-new empty database and never
        creates or modifies schema.
        """
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def dispose(self) -> None:
        """Close all pooled connections."""
        self.engine.dispose()
