import pytest

B = "/api/v1/books"


@pytest.fixture()
def seeded(make):
    rows = [
        make(1, title="Alpha", author="Ali Valiyev", genre="Roman", publication_year=1990, price=30000, available=True),
        make(2, title="beta", author="Vali Aliyev", genre="Drama", publication_year=2000, price=10000, available=False),
        make(3, title="Gamma", author="Sami", genre="roman", publication_year=2010, price=20000, available=True),
        make(4, title="100%_off", author="Sami", genre=None, publication_year=2020, price=20000, available=True),
        make(5, title="Epsilon", author="Zafar", genre="Roman", publication_year=2020, price=5000, available=True),
    ]
    return rows


def test_defaults(client, seeded):
    r = client.get(B)
    body = r.json()
    assert r.status_code == 200
    assert (body["page"], body["size"], body["total"], body["pages"]) == (1, 10, 5, 1)
    assert [b["id"] for b in body["items"]] == [b["id"] for b in seeded]
    assert r.headers["x-total-count"] == "5"


def test_pagination_pages_cover_all_without_overlap(client, seeded):
    ids = []
    for p in (1, 2, 3):
        body = client.get(B, params={"page": p, "size": 2}).json()
        assert body["pages"] == 3 and body["total"] == 5
        ids += [b["id"] for b in body["items"]]
    assert ids == sorted(set(ids)) and len(ids) == 5


def test_page_beyond_last_is_empty_not_error(client, seeded):
    r = client.get(B, params={"page": 99, "size": 2})
    assert r.status_code == 200 and r.json()["items"] == [] and r.json()["total"] == 5


@pytest.mark.parametrize("params", [
    {"page": 0}, {"page": -1}, {"size": 0}, {"size": 101}, {"page": "x"},
    {"sort_by": "color"}, {"order": "up"}, {"year_from": 1000}, {"min_price": -5}, {"available": "maybe"},
])
def test_bad_query_400(client, params):
    r = client.get(B, params=params)
    assert r.status_code == 400 and r.json()["errors"][0]["in"] == "query"


def test_filter_author_case_insensitive_contains(client, seeded):
    names = {b["title"] for b in client.get(B, params={"author": "ALI"}).json()["items"]}
    assert names == {"Alpha", "beta"}


def test_filter_title_and_like_wildcards_escaped(client, seeded):
    assert [b["title"] for b in client.get(B, params={"title": "%_"}).json()["items"]] == ["100%_off"]
    assert client.get(B, params={"title": "%"}).json()["total"] == 1


def test_filter_genre_case_insensitive_exact(client, seeded):
    assert client.get(B, params={"genre": "ROMAN"}).json()["total"] == 3


def test_filter_year_range_and_available_and_price(client, seeded):
    assert client.get(B, params={"year_from": 2000, "year_to": 2010}).json()["total"] == 2
    assert client.get(B, params={"available": "false"}).json()["total"] == 1
    assert client.get(B, params={"min_price": 10000, "max_price": 20000}).json()["total"] == 3


def test_filters_combined(client, seeded):
    body = client.get(B, params={"genre": "roman", "year_from": 2000, "available": "true"}).json()
    assert {b["title"] for b in body["items"]} == {"Gamma", "Epsilon"}


def test_inverted_ranges_400(client):
    assert client.get(B, params={"year_from": 2020, "year_to": 2000}).status_code == 400
    assert client.get(B, params={"min_price": 9, "max_price": 1}).status_code == 400


def test_sort_by_title_ignores_case(client, seeded):
    titles = [b["title"] for b in client.get(B, params={"sort_by": "title"}).json()["items"]]
    assert titles == ["100%_off", "Alpha", "beta", "Epsilon", "Gamma"]


def test_sort_price_desc_stable_tiebreak(client, seeded):
    items = client.get(B, params={"sort_by": "price", "order": "desc"}).json()["items"]
    assert [b["price"] for b in items] == [30000, 20000, 20000, 10000, 5000]
    assert items[1]["id"] < items[2]["id"]  # teng narxda id bo'yicha


def test_sort_year_asc(client, seeded):
    years = [b["publication_year"] for b in client.get(B, params={"sort_by": "publication_year"}).json()["items"]]
    assert years == sorted(years)


def test_openapi_documents_endpoints_and_no_422(client):
    spec = client.get("/openapi.json").json()
    assert set(spec["paths"]["/api/v1/books"]) == {"get", "post"}
    assert set(spec["paths"]["/api/v1/books/{book_id}"]) == {"get", "put", "patch", "delete"}
    assert "422" not in str(spec["paths"]) and "400" in spec["paths"]["/api/v1/books"]["post"]["responses"]
    assert client.get("/docs").status_code == 200 and client.get("/health").json() == {"status": "ok"}
