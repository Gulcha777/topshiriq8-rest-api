"""ISBN-13 ni normallashtirish va kontrol raqamini tekshirish."""
from __future__ import annotations

import re


def isbn13_check_digit(first12: str) -> str:
    """Dastlabki 12 ta raqam bo'yicha 13-kontrol raqamini hisoblaydi."""
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(first12))
    return str((10 - total % 10) % 10)


def normalize_isbn13(value: str) -> str:
    """Defis va bo'sh joylarni olib tashlaydi, to'g'ri bo'lmasa ValueError beradi."""
    digits = re.sub(r"[\s-]", "", value)
    if not re.fullmatch(r"\d{13}", digits):
        raise ValueError("ISBN-13 aynan 13 ta raqamdan iborat bo'lishi kerak (defis ruxsat etiladi)")
    if digits[:3] not in {"978", "979"}:
        raise ValueError("ISBN-13 978 yoki 979 bilan boshlanishi kerak")
    if isbn13_check_digit(digits[:12]) != digits[12]:
        raise ValueError("ISBN-13 kontrol raqami noto'g'ri")
    return digits


def make_isbn13(first12: str) -> str:
    """Test va seed uchun: 12 ta raqamga kontrol raqamini qo'shib, to'g'ri ISBN-13 hosil qiladi."""
    return first12 + isbn13_check_digit(first12)
