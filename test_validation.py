import pytest

from app.isbn import make_isbn13
from tests.conftest import book

B = "/api/v1/books"


@pytest.mark.parametrize("over, field", [
    ({"title": ""}, "title"),
    ({"title": "x" * 201}, "title"),
    ({"author": ""}, "author"),
    ({"isbn": "123"}, "isbn"),
    ({"isbn": "9780000000001"}, "isbn"),          # kontrol raqami xato
    ({"isbn": "9770000000000"}, "isbn"),          # 978/979 emas
    ({"publication_year": 1000}, "publication_year"),
    ({"publication_year": 3000}, "publication_year"),
    ({"publication_year": "abc"}, "publication_year"),
    ({"price": -1}, "price"),
    ({"price": 1.234}, "price"),
    ({"price": "arzon"}, "price"),
    ({"available": "balki"}, "available"),
    ({"zzz": 1}, "zzz"),
])
def test_invalid_body_returns_400(client, over, field):
    r = client.post(B, json=book(1, **over))
    assert r.status_code == 400
    body = r.json()
    assert body["status"] == 400 and body["error"] == "Bad Request"
    assert field in [e["field"] for e in body["errors"]]


def test_missing_fields_listed(client):
    r = client.post(B, json={})
    fields = {e["field"] for e in r.json()["errors"]}
    assert {"title", "author", "isbn", "publication_year", "price"} <= fields


def test_malformed_json_400(client):
    r = client.post(B, content="{bad", headers={"content-type": "application/json"})
    assert r.status_code == 400


def test_non_object_body_400(client):
    assert client.post(B, json=[1, 2]).status_code == 400


def test_non_integer_id_400(client):
    r = client.get(f"{B}/abc")
    assert r.status_code == 400 and r.json()["errors"][0]["in"] == "path"
    assert client.get(f"{B}/0").status_code == 400


def test_valid_isbn_with_hyphens_accepted(client):
    good = make_isbn13("978994300001")
    assert client.post(B, json=book(1, isbn=good[:3] + "-" + good[3:])).status_code == 201


def test_unknown_route_and_method(client):
    assert client.get("/yoq").status_code == 404
    r = client.post(f"{B}/1", json={})
    assert r.status_code == 405 and r.json()["status"] == 405
