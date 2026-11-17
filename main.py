"""FastAPI ilovasi: Book RESTful API."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from sqlalchemy import Engine

from app.config import get_settings
from app.database import Base, make_engine, make_session_factory
from app.errors import register_error_handlers
from app.routers import books

DESCRIPTION = """
**Book** resursi uchun RESTful API (Topshiriq №8).

* To'liq CRUD: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`
* Sahifalash (`page`, `size`), filtrlash va saralash (`sort_by`, `order`)
* DTO orqali validatsiya: noto'g'ri ma'lumotga **400 Bad Request** qaytadi
* Yagona xatolik formati (`status`, `error`, `message`, `path`, `errors`)
* Versiyalash: URL orqali (`/api/v1/...`)
"""


def create_app(database_url: str | None = None, engine: Engine | None = None) -> FastAPI:
    engine = engine or make_engine(database_url or get_settings().database_url)
    Base.metadata.create_all(engine)

    app = FastAPI(
        title="Books API",
        version="1.0.0",
        description=DESCRIPTION,
        openapi_tags=[{"name": "Books", "description": "Kitoblar bilan ishlash"}, {"name": "Service", "description": "Xizmat holati"}],
    )
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)

    register_error_handlers(app)
    app.include_router(books.router, prefix="/api/v1")

    @app.get("/health", tags=["Service"], summary="Xizmat holati")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title, version=app.version, description=app.description,
            routes=app.routes, tags=app.openapi_tags,
            servers=[{"url": "http://localhost:8000", "description": "Lokal server"}],
        )
        # Validatsiya xatolari bizda 400 (FastAPI'ning standart 422 si hujjatdan olib tashlanadi)
        for path_item in schema["paths"].values():
            for operation in path_item.values():
                operation.get("responses", {}).pop("422", None)
        components = schema.get("components", {}).get("schemas", {})
        components.pop("HTTPValidationError", None)
        components.pop("ValidationError", None)
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
    return app


app = create_app()
