"""Fallback-хендлер: весь бизнес-flow теперь живёт в Mini App.

Бот отвечает всем сообщениям подсказкой открыть мини-приложение.
"""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)


def create_text_router(miniapp_url: str) -> Router:
    router = Router()

    def _miniapp_markup() -> InlineKeyboardMarkup | None:
        if not miniapp_url:
            return None
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Открыть мини-приложение",
                        web_app=WebAppInfo(url=miniapp_url),
                    )
                ]
            ]
        )

    fallback_text = (
        "Теперь всё происходит внутри мини-приложения. "
        "Нажми кнопку ниже или вызови команду /start."
    )

    @router.message(F.text)
    async def on_text(message: Message) -> None:
        await message.answer(fallback_text, reply_markup=_miniapp_markup())

    @router.callback_query(F.data)
    async def on_callback(callback: CallbackQuery) -> None:
        if callback.message:
            await callback.message.answer(
                fallback_text, reply_markup=_miniapp_markup()
            )
        await callback.answer()

    @router.error()
    async def on_router_error(event) -> bool:  # type: ignore[no-untyped-def]
        logging.exception("Router-level error: %s", event.exception)
        update = event.update
        if update and update.message:
            await update.message.answer("Ошибка обработки запроса. Попробуй еще раз.")
        return True

    return router
