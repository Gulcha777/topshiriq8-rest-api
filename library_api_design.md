# Mini-tadqiqot: "Kutubxona" tizimi uchun REST API loyihasi

Resurslar: **books** (kitoblar), **members** (a'zolar), **loans** (kitob berish yozuvlari). Hamma manzillar `/api/v1` prefiksi bilan boshlanadi.
Himoyalangan (yozuvchi) amallar `Authorization: Bearer <token>` talab qiladi; token yo'q yoki yaroqsiz bo'lsa **401**.

| № | Metod | URL | Tavsif | So'rov tanasi | Javob tanasi | Status kodlari |
|---|-------|-----|--------|---------------|--------------|----------------|
| 1 | GET | /api/v1/books | Kitoblar ro'yxati (page, size, author, genre, sort_by, order) | yo'q | `{items, page, size, total, pages}` | 200, 400 |
| 2 | POST | /api/v1/books | Yangi kitob qo'shish | `{title, author, isbn, publication_year, genre, price}` | yaratilgan kitob + `Location` | 201, 400, 401, 409 |
| 3 | GET | /api/v1/books/{id} | Bitta kitob | yo'q | kitob obyekti | 200, 400, 404 |
| 4 | PUT | /api/v1/books/{id} | Kitobni to'liq almashtirish | kitobning to'liq maydonlari | yangilangan kitob | 200, 400, 401, 404, 409 |
| 5 | DELETE | /api/v1/books/{id} | Kitobni o'chirish | yo'q | yo'q | 204, 401, 404, 409 (kitob hozir qarzda) |
| 6 | GET | /api/v1/members | A'zolar ro'yxati | yo'q | `{items, page, size, total, pages}` | 200, 401 |
| 7 | POST | /api/v1/members | Yangi a'zoni ro'yxatdan o'tkazish | `{full_name, email, phone}` | yaratilgan a'zo | 201, 400, 401, 409 (email band) |
| 8 | POST | /api/v1/loans | Kitobni a'zoga berish | `{book_id, member_id, due_date}` | qarz yozuvi `{id, book_id, member_id, loaned_at, due_date, returned_at}` | 201, 400, 401, 404, 409 (kitob band) |
| 9 | POST | /api/v1/loans/{id}/return | Kitobni qaytarib olish | yo'q | yangilangan qarz yozuvi | 200, 401, 404, 409 (allaqachon qaytarilgan) |
| 10 | GET | /api/v1/members/{id}/loans | A'zoning qarzlari (status=active/returned) | yo'q | `{items, page, size, total, pages}` | 200, 400, 401, 404 |
| 11 | GET | /api/v1/books/{id}/loans | Kitobning berilish tarixi | yo'q | `{items, ...}` | 200, 401, 404 |

Dizayn qarorlari: ko'plik shakldagi otlar (`books`), fe'l emas; ichma-ich resurslar faqat bir daraja (`members/{id}/loans`);
"qaytarish" CRUD ga sig'maydigan amal bo'lgani uchun `loans/{id}/return` sub-resursi ishlatilgan; barcha ro'yxatlar sahifalanadi;
xatoliklar yagona formatda; versiya URL orqali (`/v1`).
