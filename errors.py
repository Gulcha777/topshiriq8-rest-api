"""Yagona xatolik formati va ishlovchilar (exception handlers).

Muhim: validatsiya xatolari 400 Bad Request qaytaradi (FastAPI standarti 422 o'rniga).
"""
from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app")


class ApiError(Exception):
    """Biznes qoidasi buzilganda ishlatiladi (404, 409 va h.k.)."""

    def __init__(self, status: int, message: str, errors: list[dict[str, str]] | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.errors = errors


def error_body(status: int, message: str, path: str, errors: list[dict[str, str]] | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "status": status,
        "error": HTTPStatus(status).phrase,
        "message": message,
        "path": path,
    }
    if errors:
        body["errors"] = errors
    return body


def _uz_message(err: dict[str, Any]) -> str:
    """Pydantic xatolarini o'zbekchaga o'giradi; noma'lum turlar uchun asl matn qoladi."""
    kind = err.get("type", "")
    ctx = err.get("ctx") or {}
    table = {
        "missing": "Majburiy maydon",
        "string_too_short": f"Kamida {ctx.get('min_length')} ta belgi bo'lishi kerak",
        "string_too_long": f"Ko'pi bilan {ctx.get('max_length')} ta belgi bo'lishi mumkin",
        "greater_than_equal": f"{ctx.get('ge')} dan kichik bo'lmasligi kerak",
        "greater_than": f"{ctx.get('gt')} dan katta bo'lishi kerak",
        "less_than_equal": f"{ctx.get('le')} dan katta bo'lmasligi kerak",
        "less_than": f"{ctx.get('lt')} dan kichik bo'lishi kerak",
        "int_parsing": "Butun son bo'lishi kerak",
        "int_type": "Butun son bo'lishi kerak",
        "int_from_float": "Butun son bo'lishi kerak",
        "string_type": "Matn bo'lishi kerak",
        "bool_parsing": "true yoki false bo'lishi kerak",
        "bool_type": "true yoki false bo'lishi kerak",
        "decimal_parsing": "Son bo'lishi kerak",
        "decimal_type": "Son bo'lishi kerak",
        "decimal_max_places": f"Kasr qismi ko'pi bilan {ctx.get('decimal_places')} ta raqamdan iborat bo'lishi kerak",
        "decimal_max_digits": f"Jami raqamlar soni ko'pi bilan {ctx.get('max_digits')} ta bo'lishi kerak",
        "enum": f"Ruxsat etilgan qiymatlar: {ctx.get('expected')}",
        "extra_forbidden": "Bunday maydon mavjud emas",
        "json_invalid": "JSON formati noto'g'ri",
        "model_attributes_type": "So'rov tanasi JSON obyekt bo'lishi kerak",
        "dict_type": "So'rov tanasi JSON obyekt bo'lishi kerak",
        "model_type": "So'rov tanasi JSON obyekt bo'lishi kerak",
    }
    if kind in table:
        return table[kind]
    msg = str(err.get("msg", "Qiymat noto'g'ri"))
    return msg.removeprefix("Value error, ")


def _field_errors(exc: RequestValidationError) -> list[dict[str, str]]:
    result = []
    for err in exc.errors():
        loc = [str(p) for p in err.get("loc", ())]
        where = loc[0] if loc else "body"
        field = ".".join(loc[1:]) or where
        result.append({"field": field, "message": _uz_message(err), "in": where})
    return result


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(error_body(exc.status, exc.message, request.url.path, exc.errors), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        body = error_body(400, "Kiritilgan ma'lumotlar noto'g'ri", request.url.path, _field_errors(exc))
        return JSONResponse(body, status_code=400)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        messages = {404: "Manzil topilmadi", 405: "Bu manzilda ushbu HTTP metodi qo'llab-quvvatlanmaydi"}
        message = messages.get(exc.status_code, str(exc.detail))
        return JSONResponse(
            error_body(exc.status_code, message, request.url.path),
            status_code=exc.status_code,
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Kutilmagan xatolik: %s %s", request.method, request.url.path)
        # Ichki tafsilotlar (traceback, SQL) mijozga ko'rsatilmaydi
        return JSONResponse(error_body(500, "Ichki server xatosi", request.url.path), status_code=500)
