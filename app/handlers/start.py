from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)


def create_start_router(miniapp_url: str) -> Router:
    router = Router()

    fallback_text = (
        "Привет! Это Analiticada · Нейминг.\n\n"
        "В РФ всё серьёзнее с русским языком в рекламе и вывесках, "
        "поэтому давай пофантазируем, как могли бы звучать западные бренды «по-отечественному». "
        "Открой мини-приложение — пришлёшь английское название, а я верну 5 русифицированных вариантов."
    )

    @router.message(CommandStart())
    async def on_start(message: Message) -> None:
        if miniapp_url:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Открыть мини-приложение",
                            web_app=WebAppInfo(url=miniapp_url),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Канал @analiticada",
                            url="https://t.me/analiticada",
                        )
                    ],
                ]
            )
            await message.answer(fallback_text, reply_markup=keyboard)
        else:
            await message.answer(
                fallback_text
                + "\n\n(MINIAPP_URL ещё не настроен — обратись к администратору.)"
            )

    return router
