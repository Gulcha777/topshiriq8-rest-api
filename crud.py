"""Ma'lumotlar bilan ishlash qatlami (servis): so'rovlar, filtr, saralash, sahifalash."""
from __future__ import annotations

import math
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import Book
from app.schemas import BookCreate, BookPatch, BookUpdate, SortField, SortOrder


def _duplicate_isbn(isbn: str) -> ApiError:
    return ApiError(
        409,
        f"ISBN {isbn} bilan kitob allaqachon mavjud",
        [{"field": "isbn", "message": "Bu ISBN band", "in": "body"}],
    )


def _like(value: str) -> str:
    """LIKE maxsus belgilarini (%, _) oddiy belgi sifatida qidirish uchun ekranlaydi."""
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def get_book(db: Session, book_id: int) -> Book | None:
    return db.get(Book, book_id)


def get_book_or_404(db: Session, book_id: int) -> Book:
    book = get_book(db, book_id)
    if book is None:
        raise ApiError(404, f"ID={book_id} bo'lgan kitob topilmadi")
    return book


def _isbn_taken(db: Session, isbn: str, exclude_id: int | None = None) -> bool:
    stmt = select(Book.id).where(Book.isbn == isbn)
    if exclude_id is not None:
        stmt = stmt.where(Book.id != exclude_id)
    return db.scalars(stmt).first() is not None


def _commit(db: Session, isbn: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:  # poyga holati: tekshiruvdan keyin boshqa so'rov qo'shib ulgurgan
        db.rollback()
        raise _duplicate_isbn(isbn) from exc


def create_book(db: Session, data: BookCreate) -> Book:
    if _isbn_taken(db, data.isbn):
        raise _duplicate_isbn(data.isbn)
    book = Book(**data.model_dump())
    db.add(book)
    _commit(db, data.isbn)
    return book


def replace_book(db: Session, book: Book, data: BookUpdate) -> Book:
    if _isbn_taken(db, data.isbn, exclude_id=book.id):
        raise _duplicate_isbn(data.isbn)
    for key, value in data.model_dump().items():
        setattr(book, key, value)
    _commit(db, data.isbn)
    return book


def patch_book(db: Session, book: Book, data: BookPatch) -> Book:
    changes = data.model_dump(exclude_unset=True)
    new_isbn = changes.get("isbn")
    if new_isbn is not None and _isbn_taken(db, new_isbn, exclude_id=book.id):
        raise _duplicate_isbn(new_isbn)
    for key, value in changes.items():
        setattr(book, key, value)
    _commit(db, new_isbn or book.isbn)
    return book


def delete_book(db: Session, book: Book) -> None:
    db.delete(book)
    db.commit()


def list_books(
    db: Session,
    *,
    page: int,
    size: int,
    title: str | None,
    author: str | None,
    genre: str | None,
    year_from: int | None,
    year_to: int | None,
    available: bool | None,
    min_price: Decimal | None,
    max_price: Decimal | None,
    sort_by: SortField,
    order: SortOrder,
) -> tuple[list[Book], int, int]:
    """(kitoblar, jami soni, jami sahifalar) qaytaradi."""
    if year_from is not None and year_to is not None and year_from > year_to:
        raise ApiError(400, "Kiritilgan ma'lumotlar noto'g'ri",
                       [{"field": "year_from", "message": "year_to dan katta bo'lmasligi kerak", "in": "query"}])
    if min_price is not None and max_price is not None and min_price > max_price:
        raise ApiError(400, "Kiritilgan ma'lumotlar noto'g'ri",
                       [{"field": "min_price", "message": "max_price dan katta bo'lmasligi kerak", "in": "query"}])

    conditions = []
    if title:
        conditions.append(func.lower(Book.title).like(_like(title.lower()), escape="\\"))
    if author:
        conditions.append(func.lower(Book.author).like(_like(author.lower()), escape="\\"))
    if genre:
        conditions.append(func.lower(Book.genre) == genre.lower())
    if year_from is not None:
        conditions.append(Book.publication_year >= year_from)
    if year_to is not None:
        conditions.append(Book.publication_year <= year_to)
    if available is not None:
        conditions.append(Book.available.is_(available))
    if min_price is not None:
        conditions.append(Book.price >= min_price)
    if max_price is not None:
        conditions.append(Book.price <= max_price)

    total = db.scalar(select(func.count(Book.id)).where(*conditions)) or 0

    sort_columns = {
        SortField.id: Book.id,
        SortField.title: func.lower(Book.title),  # katta-kichik harfga bog'liq bo'lmagan tartib
        SortField.author: func.lower(Book.author),
        SortField.publication_year: Book.publication_year,
        SortField.price: Book.price,
    }
    column = sort_columns[sort_by]
    primary = column.asc() if order is SortOrder.asc else column.desc()
    # Ikkinchi kalit (id) tartibni barqaror qiladi: sahifalar orasida takrorlanish/yo'qolish bo'lmaydi
    stmt = select(Book).where(*conditions).order_by(primary, Book.id.asc()).offset((page - 1) * size).limit(size)
    items = list(db.scalars(stmt).all())
    return items, total, math.ceil(total / size)
