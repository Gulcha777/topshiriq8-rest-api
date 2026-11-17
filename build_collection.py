"""Postman kolleksiyasini (v2.1) yaratadi: python postman/build_collection.py

Har bir endpoint uchun kamida bitta muvaffaqiyatli va bitta xatolik testi bor.
Testlar o'z ma'lumotini o'zi yaratadi (noyob ISBN) va oxirida o'chiradi, shuning uchun qayta-qayta ishlaydi.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
URL = "{{baseUrl}}/api/v1/books"

GOOD_BODY = {
    "title": "Postman kitobi", "author": "Test Muallif", "isbn": "{{isbn}}",
    "publication_year": 2020, "genre": "Test", "price": 45000.5, "available": True,
}

PRE_ISBN = """\
// Har so'rovdan oldin noyob va to'g'ri kontrol raqamli ISBN-13 yaratamiz
function makeIsbn() {
  var d = '978' + String(Date.now()).slice(-9);
  var sum = 0;
  for (var i = 0; i < 12; i++) { sum += parseInt(d[i], 10) * (i % 2 === 0 ? 1 : 3); }
  return d + String((10 - sum % 10) % 10);
}
pm.collectionVariables.set('isbn', makeIsbn());
"""


def req(name, method, url, tests, body=None, pre=None, query=None):
    r = {"method": method, "header": [{"key": "Content-Type", "value": "application/json"}] if body is not None else [],
         "url": {"raw": url + ("?" + "&".join(f"{k}={v}" for k, v in query) if query else ""),
                 "host": ["{{baseUrl}}"], "path": url.replace("{{baseUrl}}/", "").split("/"),
                 **({"query": [{"key": k, "value": str(v)} for k, v in query]} if query else {})}}
    if body is not None:
        r["body"] = {"mode": "raw", "raw": body if isinstance(body, str) else json.dumps(body, indent=2, ensure_ascii=False),
                     "options": {"raw": {"language": "json"}}}
    events = []
    if pre:
        events.append({"listen": "prerequest", "script": {"type": "text/javascript", "exec": pre.splitlines()}})
    events.append({"listen": "test", "script": {"type": "text/javascript", "exec": tests.strip().splitlines()}})
    return {"name": name, "event": events, "request": r}


def err_tests(code, name):
    return f"""
pm.test("Status {code} {name}", function () {{ pm.response.to.have.status({code}); }});
pm.test("Xato formati to'g'ri", function () {{
  var j = pm.response.json();
  pm.expect(j.status).to.eql({code});
  pm.expect(j).to.have.property('message');
  pm.expect(j).to.have.property('path');
}});
pm.test("Content-Type JSON", function () {{ pm.expect(pm.response.headers.get('Content-Type')).to.include('application/json'); }});
"""


SAVE_ID = """
pm.test("Status 201 Created", function () { pm.response.to.have.status(201); });
pm.test("Location sarlavhasi bor", function () { pm.expect(pm.response.headers.get('Location')).to.match(/\\/api\\/v1\\/books\\/\\d+$/); });
pm.test("Javob tanasi to'g'ri", function () {
  var j = pm.response.json();
  pm.expect(j.id).to.be.a('number');
  pm.expect(j.title).to.eql('Postman kitobi');
  pm.expect(j.isbn).to.eql(pm.collectionVariables.get('isbn'));
  pm.expect(j.price).to.eql(45000.5);
  pm.collectionVariables.set('bookId', j.id);
});
"""

items_ok = [
    req("POST /books - kitob yaratish (201)", "POST", URL, SAVE_ID, GOOD_BODY, pre=PRE_ISBN),
    req("GET /books/{id} - bitta kitob (200)", "GET", URL + "/{{bookId}}", """
pm.test("Status 200 OK", function () { pm.response.to.have.status(200); });
pm.test("ID mos keladi", function () { pm.expect(pm.response.json().id).to.eql(pm.collectionVariables.get('bookId')); });
pm.test("Barcha maydonlar bor", function () {
  pm.expect(pm.response.json()).to.have.all.keys('id','title','author','isbn','publication_year','genre','price','available');
});
"""),
    req("GET /books - sahifalangan ro'yxat (200)", "GET", URL, """
pm.test("Status 200 OK", function () { pm.response.to.have.status(200); });
pm.test("Sahifalash tuzilmasi", function () {
  var j = pm.response.json();
  pm.expect(j).to.have.all.keys('items','page','size','total','pages');
  pm.expect(j.items).to.be.an('array').with.lengthOf.at.most(2);
  pm.expect(j.page).to.eql(1);
  pm.expect(j.size).to.eql(2);
  pm.expect(j.total).to.be.at.least(1);
});
pm.test("X-Total-Count sarlavhasi total ga teng", function () {
  pm.expect(parseInt(pm.response.headers.get('X-Total-Count'), 10)).to.eql(pm.response.json().total);
});
""", query=[("page", 1), ("size", 2)]),
    req("GET /books - filtr va saralash (200)", "GET", URL, """
pm.test("Status 200 OK", function () { pm.response.to.have.status(200); });
pm.test("Filtr: faqat janr=Test, narx kamayish tartibida", function () {
  var items = pm.response.json().items;
  pm.expect(items.length).to.be.at.least(1);
  items.forEach(function (b) { pm.expect(b.genre).to.eql('Test'); });
  for (var i = 1; i < items.length; i++) { pm.expect(items[i-1].price).to.be.at.least(items[i].price); }
});
""", query=[("genre", "test"), ("sort_by", "price"), ("order", "desc")]),
    req("PUT /books/{id} - to'liq almashtirish (200)", "PUT", URL + "/{{bookId}}", """
pm.test("Status 200 OK", function () { pm.response.to.have.status(200); });
pm.test("Maydonlar almashtirildi", function () {
  var j = pm.response.json();
  pm.expect(j.title).to.eql('Yangilangan nom');
  pm.expect(j.price).to.eql(50000);
  pm.expect(j.genre).to.eql(null);
  pm.expect(j.id).to.eql(pm.collectionVariables.get('bookId'));
});
""", {**GOOD_BODY, "title": "Yangilangan nom", "price": 50000, "genre": None}),
    req("PATCH /books/{id} - qisman yangilash (200)", "PATCH", URL + "/{{bookId}}", """
pm.test("Status 200 OK", function () { pm.response.to.have.status(200); });
pm.test("Faqat narx o'zgardi", function () {
  var j = pm.response.json();
  pm.expect(j.price).to.eql(55000);
  pm.expect(j.title).to.eql('Yangilangan nom');
});
""", {"price": 55000}),
]

items_err = [
    req("POST /books - noto'g'ri ma'lumot (400)", "POST", URL, err_tests(400, "Bad Request") + """
pm.test("errors ro'yxatida title, isbn, price bor", function () {
  var fields = pm.response.json().errors.map(function (e) { return e.field; });
  pm.expect(fields).to.include.members(['title', 'isbn', 'price']);
});
""", {"title": "", "author": "A", "isbn": "123", "publication_year": 2020, "price": -5}),
    req("POST /books - takroriy ISBN (409)", "POST", URL, err_tests(409, "Conflict"), GOOD_BODY),
    req("GET /books - noto'g'ri query (400)", "GET", URL, err_tests(400, "Bad Request") + """
pm.test("Xato query'da", function () { pm.expect(pm.response.json().errors[0].in).to.eql('query'); });
""", query=[("page", 0), ("size", 1000)]),
    req("GET /books/{id} - mavjud emas (404)", "GET", URL + "/999999999", err_tests(404, "Not Found")),
    req("GET /books/{id} - ID raqam emas (400)", "GET", URL + "/abc", err_tests(400, "Bad Request")),
    req("PUT /books/{id} - mavjud emas (404)", "PUT", URL + "/999999999", err_tests(404, "Not Found"), GOOD_BODY),
    req("PUT /books/{id} - noto'g'ri ma'lumot (400)", "PUT", URL + "/{{bookId}}", err_tests(400, "Bad Request"), {"title": "faqat nom"}),
    req("PATCH /books/{id} - bo'sh tana (400)", "PATCH", URL + "/{{bookId}}", err_tests(400, "Bad Request"), {}),
    req("PATCH /books/{id} - mavjud emas (404)", "PATCH", URL + "/999999999", err_tests(404, "Not Found"), {"price": 1}),
]

items_del = [
    req("DELETE /books/{id} - o'chirish (204)", "DELETE", URL + "/{{bookId}}", """
pm.test("Status 204 No Content", function () { pm.response.to.have.status(204); });
pm.test("Javob tanasi bo'sh", function () { pm.expect(pm.response.text()).to.eql(''); });
"""),
    req("GET /books/{id} - o'chirilgandan keyin (404)", "GET", URL + "/{{bookId}}", err_tests(404, "Not Found")),
    req("DELETE /books/{id} - qayta o'chirish (404)", "DELETE", URL + "/{{bookId}}", err_tests(404, "Not Found")),
    req("DELETE /books/{id} - ID raqam emas (400)", "DELETE", URL + "/abc", err_tests(400, "Bad Request")),
]

collection = {
    "info": {"name": "Books API - Topshiriq 8", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
             "description": "Har bir endpoint uchun muvaffaqiyatli va xatolik testlari. Tartib bilan (Runner) ishga tushiring."},
    "variable": [{"key": "baseUrl", "value": "http://localhost:8000"}, {"key": "bookId", "value": ""}, {"key": "isbn", "value": ""}],
    "item": [
        {"name": "1. Muvaffaqiyatli holatlar", "item": items_ok},
        {"name": "2. Xatolik holatlari", "item": items_err},
        {"name": "3. O'chirish", "item": items_del},
    ],
}
env = {"name": "Local", "values": [{"key": "baseUrl", "value": "http://localhost:8000", "enabled": True}], "_postman_variable_scope": "environment"}
(HERE / "books_api.postman_collection.json").write_text(json.dumps(collection, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(HERE / "local.postman_environment.json").write_text(json.dumps(env, indent=2) + "\n", encoding="utf-8")
print("OK:", sum(len(f["item"]) for f in collection["item"]), "ta so'rov")
