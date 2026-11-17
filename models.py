"""ORM model: Book."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_books_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    author: Mapped[str] = mapped_column(String(100), index=True)
    isbn: Mapped[str] = mapped_column(String(13), unique=True)
    publication_year: Mapped[int]
    genre: Mapped[str | None] = mapped_column(String(50), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    available: Mapped[bool] = mapped_column(default=True)
