"""DTO (Data Transfer Object) sxemalari: so'rov va javob tuzilmalari, validatsiya qoidalari."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator, model_validator

from app.isbn import normalize_isbn13

MIN_YEAR = 1450  # Gutenberg bosmaxonasi

Title = Annotated[str, Field(min_length=1, max_length=200, description="Kitob nomi")]
Author = Annotated[str, Field(min_length=1, max_length=100, description="Muallif")]
Genre = Annotated[str, Field(min_length=1, max_length=50, description="Janr")]
Year = Annotated[int, Field(ge=MIN_YEAR, description="Nashr yili (1450 dan joriy yilgacha)")]
# Narx bazada aniq (Decimal) saqlanadi, JSON javobda oddiy son sifatida qaytadi
Price = Annotated[
    Decimal,
    Field(ge=0, max_digits=8, decimal_places=2, description="Narx (so'm), 0 dan 999999.99 gacha, kasr qismi ko'pi bilan 2 ta raqam"),
    PlainSerializer(lambda v: float(v), return_type=float, when_used="json"),
]


class _Strict(BaseModel):
    """Umumiy sozlamalar: bo'sh joylarni qirqish, noma'lum maydonlarni rad etish."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


def _check_isbn(value: str) -> str:
    return normalize_isbn13(value)


def _check_year(value: int) -> int:
    if value > date.today().year:
        raise ValueError(f"Nashr yili {date.today().year} dan katta bo'lishi mumkin emas")
    return value


class BookCreate(_Strict):
    """Yangi kitob yaratish (POST) va to'liq almashtirish (PUT) uchun."""

    title: Title
    author: Author
    isbn: Annotated[str, Field(description="ISBN-13 (defis bilan yoki defissiz); saqlashda defissiz ko'rinishga keltiriladi")]
    publication_year: Year
    genre: Genre | None = None
    price: Price
    available: bool = True

    _v_isbn = field_validator("isbn")(_check_isbn)
    _v_year = field_validator("publication_year")(_check_year)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "title": "O'tkan kunlar",
                    "author": "Abdulla Qodiriy",
                    "isbn": "978-9943-00001-8",
                    "publication_year": 1926,
                    "genre": "Roman",
                    "price": 59000.00,
                    "available": True,
                }
            ]
        },
    )


class BookUpdate(BookCreate):
    """PUT: resursning TO'LIQ yangi ko'rinishi. Yuborilmagan ixtiyoriy maydonlar standart qiymatga qaytadi."""


class BookPatch(_Strict):
    """PATCH: faqat yuborilgan maydonlar o'zgaradi."""

    title: Title = None  # type: ignore[assignment]
    author: Author = None  # type: ignore[assignment]
    isbn: str = None  # type: ignore[assignment]
    publication_year: Year = None  # type: ignore[assignment]
    genre: Genre | None = None
    price: Price = None  # type: ignore[assignment]
    available: bool = None  # type: ignore[assignment]

    _v_isbn = field_validator("isbn")(_check_isbn)
    _v_year = field_validator("publication_year")(_check_year)

    @model_validator(mode="after")
    def _at_least_one(self) -> "BookPatch":
        if not self.model_fields_set:
            raise ValueError("Kamida bitta maydon yuborilishi kerak")
        return self


class BookRead(BaseModel):
    """Javobda qaytariladigan kitob."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    isbn: str
    publication_year: int
    genre: str | None
    price: Price
    available: bool


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Sahifalangan ro'yxat."""

    items: list[T]
    page: int = Field(description="Joriy sahifa (1 dan boshlanadi)")
    size: int = Field(description="Sahifadagi elementlar soni (so'ralgan)")
    total: int = Field(description="Filtrga mos jami elementlar soni")
    pages: int = Field(description="Jami sahifalar soni")


class SortField(str, Enum):
    id = "id"
    title = "title"
    author = "author"
    publication_year = "publication_year"
    price = "price"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class FieldError(BaseModel):
    field: str = Field(description="Xato maydon nomi")
    message: str = Field(description="Xato tavsifi")
    location: str = Field(alias="in", description="Qayerda: body, query yoki path")

    model_config = ConfigDict(populate_by_name=True)


class ErrorResponse(BaseModel):
    """Barcha xatoliklar uchun yagona format."""

    status: int
    error: str = Field(description="HTTP status nomi")
    message: str
    path: str
    errors: list[FieldError] | None = Field(default=None, description="Validatsiya xatolari ro'yxati (faqat 400)")
