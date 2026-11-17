# Books REST API (Topshiriq №8)

FastAPI + SQLAlchemy asosidagi **Book** resursi uchun RESTful API: CRUD, sahifalash, filtrlash, saralash, DTO validatsiya (xato bo'lsa **400**), Swagger/OpenAPI va Postman kolleksiyasi.

Talaba: Xamroyeva Gulruh, guruh 1-1DIM-24

## Tezkor ishga tushirish

```bash
./run.sh          # Windows: run.bat
```

Server: http://localhost:8000 · Swagger UI: http://localhost:8000/docs · ReDoc: /redoc · OpenAPI: /openapi.json

Standart baza SQLite (`books.db`). PostgreSQL uchun `.env.example` ni `.env` ga nusxalab `DATABASE_URL` ni o'zgartiring va `requirements.txt` da `psycopg2-binary` qatorini oching.

## Endpointlar (`/api/v1`)

| Metod | URL | Tavsif | Muvaffaqiyat | Xatolar |
|---|---|---|---|---|
| POST | /books | Yaratish | 201 + Location | 400, 409 |
| GET | /books | Ro'yxat: `page`, `size`, `title`, `author`, `genre`, `year_from`, `year_to`, `available`, `min_price`, `max_price`, `sort_by`, `order` | 200 | 400 |
| GET | /books/{id} | Bitta kitob | 200 | 400, 404 |
| PUT | /books/{id} | To'liq almashtirish | 200 | 400, 404, 409 |
| PATCH | /books/{id} | Qisman yangilash | 200 | 400, 404, 409 |
| DELETE | /books/{id} | O'chirish | 204 | 400, 404 |

Xatolik formati (hamma xatolar uchun yagona):

```json
{"status": 400, "error": "Bad Request", "message": "Kiritilgan ma'lumotlar noto'g'ri", "path": "/api/v1/books",
 "errors": [{"field": "isbn", "message": "ISBN-13 kontrol raqami noto'g'ri", "in": "body"}]}
```

Validatsiya: nom 1-200, muallif 1-100, ISBN-13 (kontrol raqami tekshiriladi, defis ruxsat), yil 1450..joriy yil, narx >= 0 (ko'pi bilan 2 ta kasr raqam), noma'lum maydonlar rad etiladi.

## Testlar

```bash
./test.sh                                   # pytest (SQLite xotirada)
TEST_POSTGRES_URL=postgresql+psycopg2://user:pass@localhost/db_test ./test.sh   # ixtiyoriy: haqiqiy PostgreSQL
```

## Postman

`postman/books_api.postman_collection.json` va `postman/local.postman_environment.json` ni Postman ga import qiling (Import), serverni ishga tushiring va Collection Runner bilan yurgizing.
Har endpoint uchun kamida bitta muvaffaqiyatli va bitta xatolik testi bor (Tests yorlig'ida `pm.test`/`pm.expect`).
Konsolda: `npx newman run postman/books_api.postman_collection.json -e postman/local.postman_environment.json`.
Kolleksiyani qayta yaratish: `python postman/build_collection.py`.

## Hujjatlar

- `docs/openapi.json` — OpenAPI 3.1 sxemasi
- `docs/swagger_ui.png`, `docs/swagger_ui_get_books.png` — Swagger UI skrinshotlari
- `docs/library_api_design.md` — "Kutubxona" tizimi REST endpointlari jadvali (mini-tadqiqot)

## Tuzilma

```
app/        main.py (ilova), routers/books.py, schemas.py (DTO), crud.py, errors.py, models.py, isbn.py, seed.py
tests/      pytest testlari
postman/    kolleksiya, muhit, generator
docs/       OpenAPI, skrinshotlar, dizayn
```
