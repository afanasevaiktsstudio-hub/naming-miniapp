"""FastAPI-приложение для Telegram Mini App.

Эндпоинты:
- POST /api/variants  — сгенерировать 5 вариантов
- POST /api/select    — сохранить выбор пользователя
- GET  /api/session   — текущее состояние пользователя
- GET  /api/health    — healthcheck для Railway

Авторизация:
Заголовок `X-Telegram-Init-Data` с подписанными данными от Telegram WebApp.
Проверка по алгоритму Telegram (HMAC SHA256 от BOT_TOKEN).
В режиме `DEBUG_USER_ID > 0` разрешаем заголовок `X-Debug-User` для локальной разработки
без Telegram (запускать ТОЛЬКО не в проде).
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.init_data import InitData, InitDataError, InitDataUser, verify_init_data
from app.config import Settings
from app.services.naming_service import NamingService
from app.storage.sqlite_store import SQLiteStore, UserSession

logger = logging.getLogger(__name__)


class VariantOut(BaseModel):
    index: int
    title: str
    translit: str | None = None
    rationale: str | None = None


class SessionStateOut(BaseModel):
    source_name: str | None
    variants: list[VariantOut]
    selected_index: int | None


class VariantsResponse(BaseModel):
    variants: list[VariantOut]
    session: SessionStateOut


class VariantsRequest(BaseModel):
    source_name: str = Field(min_length=1, max_length=200)


class SelectRequest(BaseModel):
    index: int = Field(ge=0, le=4)


def _variants_to_out(variants: list[dict[str, str]]) -> list[VariantOut]:
    out: list[VariantOut] = []
    for idx, item in enumerate(variants):
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        comment = str(item.get("comment", "")).strip() or None
        style = str(item.get("style", "")).strip() or None
        out.append(
            VariantOut(
                index=idx,
                title=title,
                translit=style,
                rationale=comment,
            )
        )
    return out


def _session_to_out(session: UserSession | None) -> SessionStateOut:
    if session is None:
        return SessionStateOut(source_name=None, variants=[], selected_index=None)
    variants = _variants_to_out(session.variants)
    selected_index: int | None = None
    if session.selected_title:
        for v in variants:
            if v.title == session.selected_title:
                selected_index = v.index
                break
    return SessionStateOut(
        source_name=session.source_name,
        variants=variants,
        selected_index=selected_index,
    )


def create_app(
    settings: Settings,
    store: SQLiteStore,
    naming_service: NamingService,
) -> FastAPI:
    app = FastAPI(
        title="Analiticada Naming Mini App API",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    origins = list(settings.api_cors_origins) or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    def require_user(
        request: Request,
        x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
        x_debug_user: str | None = Header(default=None, alias="X-Debug-User"),
    ) -> InitDataUser:
        if x_telegram_init_data:
            try:
                data: InitData = verify_init_data(
                    x_telegram_init_data, bot_token=settings.bot_token
                )
            except InitDataError as exc:
                logger.info("initData rejected: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"initData invalid: {exc}",
                ) from exc
            return data.user
        if settings.debug_user_id > 0 and x_debug_user == "1":
            logger.warning(
                "Using DEBUG user %s for request %s %s",
                settings.debug_user_id,
                request.method,
                request.url.path,
            )
            return InitDataUser(id=settings.debug_user_id, first_name="debug")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Telegram-Init-Data header is required",
        )

    @app.exception_handler(HTTPException)
    async def _http_exc_handler(request: Request, exc: HTTPException) -> JSONResponse:  # type: ignore[unused-variable]
        body: dict[str, Any] = {"message": str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.get("/api/health")
    async def health() -> dict[str, str]:  # type: ignore[unused-variable]
        return {"status": "ok"}

    @app.get("/api/session", response_model=SessionStateOut)
    async def get_session(user: InitDataUser = Depends(require_user)) -> SessionStateOut:  # type: ignore[unused-variable]
        session = store.get_session(user.id)
        return _session_to_out(session)

    @app.post("/api/variants", response_model=VariantsResponse)
    async def post_variants(  # type: ignore[unused-variable]
        payload: VariantsRequest,
        user: InitDataUser = Depends(require_user),
    ) -> VariantsResponse:
        source = payload.source_name.strip()
        if len(source) > settings.max_input_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"source_name too long (>{settings.max_input_length})",
            )
        if not store.try_consume(user.id, "text", settings.daily_text_limit):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Дневной лимит исчерпан. Возвращайся завтра.",
            )
        try:
            variants = await naming_service.generate(source)
        except Exception as exc:
            logger.exception("NamingService.generate failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Не удалось сгенерировать варианты. Попробуй еще раз.",
            ) from exc

        session = UserSession(source_name=source, variants=variants, selected_title=None)
        store.set_session(user.id, session)
        out = _session_to_out(session)
        return VariantsResponse(variants=out.variants, session=out)

    @app.post("/api/select", response_model=SessionStateOut)
    async def post_select(  # type: ignore[unused-variable]
        payload: SelectRequest,
        user: InitDataUser = Depends(require_user),
    ) -> SessionStateOut:
        session = store.get_session(user.id)
        if session is None or not session.variants:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сначала сгенерируй варианты.",
            )
        if payload.index < 0 or payload.index >= len(session.variants):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Индекс вне диапазона доступных вариантов.",
            )
        selected_title = str(session.variants[payload.index].get("title", "")).strip()
        if not selected_title:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Выбранный вариант пуст.",
            )
        store.set_selected_title(user.id, selected_title)
        updated = store.get_session(user.id)
        return _session_to_out(updated)

    return app
