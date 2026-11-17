"""Book resursi: /api/v1/books"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Iterator

from fastapi import APIRouter, Depends, Path, Query, Request, Response
from sqlalchemy.orm import Session

from app import crud
from app.schemas import (
    BookCreate,
    BookPatch,
    BookRead,
    BookUpdate,
    ErrorResponse,
    Page,
    SortField,
    SortOrder,
)

router = APIRouter(prefix="/books", tags=["Books"])


def get_db(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]

R400 = {"model": ErrorResponse, "description": "Validatsiya xatosi: so'rov ma'lumotlari noto'g'ri"}
R404 = {"model": ErrorResponse, "description": "Kitob topilmadi"}
R409 = {"model": ErrorResponse, "description": "Konflikt: bu ISBN bilan kitob allaqachon mavjud"}


BookIdPath = Annotated[int, Path(ge=1, description="Kitob identifikatori (1 dan boshlanuvchi butun son)", examples=[1])]


@router.post(
    "",
    response_model=BookRead,
    status_code=201,
    summary="Yangi kitob yaratish",
    responses={400: R400, 409: R409},
)
def create_book(payload: BookCreate, request: Request, response: Response, db: DbSession):
    """Yangi kitob yaratadi. Muvaffaqiyatda **201 Created** va yangi resurs manzili `Location` sarlavhasida qaytadi."""
    book = crud.create_book(db, payload)
    response.headers["Location"] = str(request.url_for("get_book", book_id=book.id))
    return book


@router.get(
    "",
    response_model=Page[BookRead],
    summary="Kitoblar ro'yxati (sahifalash, filtr, saralash)",
    responses={400: R400},
)
def list_books(
    response: Response,
    db: DbSession,
    page: Annotated[int, Query(ge=1, description="Sahifa raqami (1 dan boshlanadi)")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Sahifadagi elementlar soni (1-100)")] = 10,
    title: Annotated[str | None, Query(min_length=1, max_length=200, description="Nomida shu matn bor (katta-kichik harf farqsiz)")] = None,
    author: Annotated[str | None, Query(min_length=1, max_length=100, description="Muallif nomida shu matn bor (katta-kichik harf farqsiz)")] = None,
    genre: Annotated[str | None, Query(min_length=1, max_length=50, description="Aynan shu janr (katta-kichik harf farqsiz)")] = None,
    year_from: Annotated[int | None, Query(ge=1450, description="Nashr yili shundan kam emas")] = None,
    year_to: Annotated[int | None, Query(ge=1450, description="Nashr yili shundan ko'p emas")] = None,
    available: Annotated[bool | None, Query(description="Mavjudlik: true yoki false")] = None,
    min_price: Annotated[Decimal | None, Query(ge=0, description="Narx shundan kam emas")] = None,
    max_price: Annotated[Decimal | None, Query(ge=0, description="Narx shundan ko'p emas")] = None,
    sort_by: Annotated[SortField, Query(description="Saralash maydoni")] = SortField.id,
    order: Annotated[SortOrder, Query(description="Saralash yo'nalishi")] = SortOrder.asc,
):
    """Filtrlangan, saralangan va sahifalangan ro'yxat. Jami soni `X-Total-Count` sarlavhasida ham qaytadi.

    So'ralgan sahifa oxirgisidan keyin bo'lsa, xato emas, bo'sh `items` qaytadi.
    """
    items, total, pages = crud.list_books(
        db, page=page, size=size, title=title, author=author, genre=genre,
        year_from=year_from, year_to=year_to, available=available,
        min_price=min_price, max_price=max_price, sort_by=sort_by, order=order,
    )
    response.headers["X-Total-Count"] = str(total)
    return Page[BookRead](items=items, page=page, size=size, total=total, pages=pages)


@router.get(
    "/{book_id}",
    response_model=BookRead,
    summary="Kitobni ID bo'yicha olish",
    responses={400: R400, 404: R404},
)
def get_book(book_id: BookIdPath, db: DbSession):
    return crud.get_book_or_404(db, book_id)


@router.put(
    "/{book_id}",
    response_model=BookRead,
    summary="Kitobni to'liq almashtirish",
    responses={400: R400, 404: R404, 409: R409},
)
def replace_book(book_id: BookIdPath, payload: BookUpdate, db: DbSession):
    """Resursning **to'liq** yangi ko'rinishini yuboring. Yuborilmagan ixtiyoriy maydonlar standart qiymatga qaytadi
    (`genre` bo'sh, `available` true). Bir xil so'rovni takrorlash natijani o'zgartirmaydi (idempotent)."""
    book = crud.get_book_or_404(db, book_id)
    return crud.replace_book(db, book, payload)


@router.patch(
    "/{book_id}",
    response_model=BookRead,
    summary="Kitobni qisman yangilash",
    responses={400: R400, 404: R404, 409: R409},
)
def patch_book(book_id: BookIdPath, payload: BookPatch, db: DbSession):
    """Faqat yuborilgan maydonlar o'zgaradi. `genre` ni tozalash uchun `null` yuboring."""
    book = crud.get_book_or_404(db, book_id)
    return crud.patch_book(db, book, payload)


@router.delete(
    "/{book_id}",
    status_code=204,
    summary="Kitobni o'chirish",
    responses={400: R400, 404: R404},
)
def delete_book(book_id: BookIdPath, db: DbSession):
    """Muvaffaqiyatda **204 No Content** (javob tanasi yo'q). Qayta o'chirishga urinish 404 beradi."""
    crud.delete_book(db, crud.get_book_or_404(db, book_id))
    return Response(status_code=204)
