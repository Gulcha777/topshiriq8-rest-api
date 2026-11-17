from tests.conftest import book

B = "/api/v1/books"


def test_create_returns_201_and_location(client):
    r = client.post(B, json=book(1))
    assert r.status_code == 201
    body = r.json()
    assert r.headers["location"].endswith(f"{B}/{body['id']}")
    assert body["price"] == 11000 and body["available"] is True


def test_create_normalizes_isbn_and_strips_title(client):
    from app.isbn import make_isbn13
    good = make_isbn13("978000000001")
    r = client.post(B, json=book(1, isbn=f"{good[:3]}-{good[3:]}", title="  Bo'sh  "))
    assert r.status_code == 201
    assert r.json()["isbn"] == good and r.json()["title"] == "Bo'sh"


def test_get_by_id(client, make):
    b = make(1)
    r = client.get(f"{B}/{b['id']}")
    assert r.status_code == 200 and r.json() == b


def test_get_unknown_is_404(client):
    r = client.get(f"{B}/999")
    assert r.status_code == 404
    assert r.json()["status"] == 404 and r.json()["path"] == f"{B}/999"


def test_put_replaces_and_is_idempotent(client, make):
    b = make(1)
    new = book(1, title="Yangi nom", genre=None, price=500)
    r1 = client.put(f"{B}/{b['id']}", json=new)
    r2 = client.put(f"{B}/{b['id']}", json=new)
    assert r1.status_code == r2.status_code == 200
    assert r1.json() == r2.json()
    assert r1.json()["title"] == "Yangi nom" and r1.json()["genre"] is None


def test_put_unknown_404_and_invalid_400(client, make):
    assert client.put(f"{B}/999", json=book(1)).status_code == 404
    b = make(1)
    assert client.put(f"{B}/{b['id']}", json={"title": "x"}).status_code == 400


def test_patch_partial(client, make):
    b = make(1)
    r = client.patch(f"{B}/{b['id']}", json={"price": 1234.5})
    assert r.status_code == 200
    assert r.json()["price"] == 1234.5 and r.json()["title"] == b["title"]
    r = client.patch(f"{B}/{b['id']}", json={"genre": None})
    assert r.json()["genre"] is None


def test_patch_empty_body_400(client, make):
    b = make(1)
    assert client.patch(f"{B}/{b['id']}", json={}).status_code == 400


def test_delete_204_then_404(client, make):
    b = make(1)
    r = client.delete(f"{B}/{b['id']}")
    assert r.status_code == 204 and r.content == b""
    assert client.get(f"{B}/{b['id']}").status_code == 404
    assert client.delete(f"{B}/{b['id']}").status_code == 404


def test_duplicate_isbn_409(client, make):
    make(1)
    r = client.post(B, json=book(2, isbn=book(1)["isbn"]))
    assert r.status_code == 409 and r.json()["errors"][0]["field"] == "isbn"


def test_put_same_isbn_on_self_ok_but_other_409(client, make):
    a, b = make(1), make(2)
    assert client.put(f"{B}/{a['id']}", json=book(1, title="X")).status_code == 200
    assert client.put(f"{B}/{a['id']}", json=book(1, isbn=b["isbn"])).status_code == 409
    assert client.patch(f"{B}/{a['id']}", json={"isbn": b["isbn"]}).status_code == 409
