from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool

from app.database import make_engine
from app.isbn import make_isbn13
from app.main import create_app


@pytest.fixture()
def client(tmp_path):
    url = os.getenv("TEST_POSTGRES_URL")
    if url:
        engine = make_engine(url)
        from app.database import Base
        Base.metadata.drop_all(engine)
    else:
        engine = make_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    app = create_app(engine=engine)
    with TestClient(app) as c:
        yield c
    engine.dispose()


def book(n: int = 1, **over):
    data = {
        "title": f"Kitob {n}", "author": "Muallif A", "isbn": make_isbn13(f"9780000{n:05d}"),
        "publication_year": 2000 + n % 20, "genre": "Roman", "price": 10000 + n * 1000, "available": True,
    }
    data.update(over)
    return data


@pytest.fixture()
def make(client):
    def _make(n=1, **over):
        r = client.post("/api/v1/books", json=book(n, **over))
        assert r.status_code == 201, r.text
        return r.json()
    return _make
