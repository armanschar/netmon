"""Tests for GET /health."""

import pytest
import sqlalchemy.exc
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    """A test client backed by a throwaway SQLite file.

    A file (not `sqlite://`) is used because an in-memory SQLite database is
    per-connection, so a pooled engine could see a different, empty database.
    """
    db_path = (tmp_path / "test.db").as_posix()
    app = create_app(Settings(database_url=f"sqlite:///{db_path}"))
    # The context manager runs the lifespan, so startup/shutdown really execute.
    with TestClient(app) as test_client:
        yield test_client


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_reports_503_when_database_is_down(client, monkeypatch):
    def boom() -> None:
        raise sqlalchemy.exc.OperationalError("SELECT 1", {}, Exception("disk I/O error"))

    monkeypatch.setattr(client.app.state.database, "ping", boom)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}


def test_health_creates_no_tables(client):
    client.get("/health")

    tables = inspect(client.app.state.database.engine).get_table_names()

    assert tables == []
