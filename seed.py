"""Namunaviy kitoblar (sahifalash va filtrlarni sinash uchun).

Ishga tushirish:  python -m app.seed          (bo'sh bazaga)
                  python -m app.seed --reset  (avval hammasini o'chirib)
ISBN raqamlari to'g'ri kontrol raqamiga ega, lekin namunaviy (haqiqiy nashrlarga mos kelmaydi).
"""
from __future__ import annotations

import sys
from decimal import Decimal

from sqlalchemy import delete, func, select

from app.config import get_settings
from app.database import Base, make_engine, make_session_factory
from app.isbn import make_isbn13
from app.models import Book

# (nomi, muallif, yil, janr, narx)
SAMPLE_BOOKS = [
    ("O'tkan kunlar", "Abdulla Qodiriy", 1926, "Roman", "59000.00"),
    ("Mehrobdan chayon", "Abdulla Qodiriy", 1929, "Roman", "52000.00"),
    ("Kecha va kunduz", "Cho'lpon", 1936, "Roman", "64000.00"),
    ("Sarob", "Abdulla Qahhor", 1937, "Roman", "48000.00"),
    ("Qutlug' qon", "Oybek", 1940, "Roman", "57000.00"),
    ("Navoiy", "Oybek", 1944, "Roman", "61000.00"),
    ("1984", "George Orwell", 1949, "Fantastika", "69000.00"),
    ("Hayvonlar fermasi", "George Orwell", 1945, "Satira", "39000.00"),
    ("Alximik", "Paulo Coelho", 1988, "Roman", "55000.00"),
    ("Kichkina shahzoda", "Antoine de Saint-Exupery", 1943, "Ertak", "42000.00"),
    ("Robinzon Kruzo", "Daniel Defoe", 1719, "Sarguzasht", "46000.00"),
    ("Don Kixot", "Miguel de Cervantes", 1605, "Roman", "72000.00"),
    ("Jinoyat va jazo", "Fyodor Dostoevsky", 1866, "Roman", "78000.00"),
    ("Urush va tinchlik", "Lev Tolstoy", 1869, "Roman", "98000.00"),
    ("Hamlet", "William Shakespeare", 1603, "Drama", "37000.00"),
    ("Qizil rangdagi etyud", "Arthur Conan Doyle", 1887, "Detektiv", "44000.00"),
    ("Fluent Python", "Luciano Ramalho", 2015, "Dasturlash", "189000.00"),
    ("Clean Code", "Robert C. Martin", 2008, "Dasturlash", "165000.00"),
    ("Design Patterns", "Erich Gamma", 1994, "Dasturlash", "175000.00"),
    ("The Pragmatic Programmer", "Andrew Hunt", 1999, "Dasturlash", "158000.00"),
    ("Introduction to Algorithms", "Thomas H. Cormen", 1990, "Dasturlash", "210000.00"),
    ("Python Crash Course", "Eric Matthes", 2015, "Dasturlash", "149000.00"),
    ("Sapiens", "Yuval Noah Harari", 2011, "Tarix", "85000.00"),
    ("Atomic Habits", "James Clear", 2018, "Psixologiya", "76000.00"),
    ("Dune", "Frank Herbert", 1965, "Fantastika", "81000.00"),
]


def seed(session) -> int:
    """Bo'sh bazani to'ldiradi; yaratilgan kitoblar sonini qaytaradi (bo'sh bo'lmasa 0)."""
    if (session.scalar(select(func.count(Book.id))) or 0) > 0:
        return 0
    for i, (title, author, year, genre, price) in enumerate(SAMPLE_BOOKS, start=1):
        session.add(
            Book(
                title=title, author=author, publication_year=year, genre=genre,
                price=Decimal(price), isbn=make_isbn13(f"9789943{i:05d}"), available=(i % 5 != 0),
            )
        )
    session.commit()
    return len(SAMPLE_BOOKS)


def main() -> None:
    engine = make_engine(get_settings().database_url)
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as session:
        if "--reset" in sys.argv:
            session.execute(delete(Book))
            session.commit()
        created = seed(session)
    print(f"Seed: {created} ta kitob qo'shildi" if created else "Baza bo'sh emas, seed o'tkazib yuborildi (qaytadan: --reset).")


if __name__ == "__main__":
    main()
