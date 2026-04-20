import asyncio
import logging

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.types import (
    BotCommand,
    ErrorEvent,
    MenuButtonWebApp,
    WebAppInfo,
)

from app.api.server import create_app
from app.config import load_settings
from app.handlers.start import create_start_router
from app.handlers.text import create_text_router
from app.services.naming_service import NamingService
from app.storage.sqlite_store import SQLiteStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _run_api(app, host: str, port: int) -> None:
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)
    await server.serve()


async def _run_bot(settings, naming_service: NamingService, store: SQLiteStore) -> None:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(create_start_router(settings.miniapp_url))
    dp.include_router(create_text_router(settings.miniapp_url))

    @dp.error()
    async def on_error(event: ErrorEvent) -> bool:
        logger.exception("Unhandled dispatcher error: %s", event.exception)
        if event.update and event.update.message:
            await event.update.message.answer("Внутренняя ошибка. Попробуй еще раз.")
        return True

    await bot.set_my_commands([BotCommand(command="start", description="Открыть мини-приложение")])
    if settings.miniapp_url:
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="Открыть",
                    web_app=WebAppInfo(url=settings.miniapp_url),
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to set menu button: %s", exc)

    await dp.start_polling(bot)


async def main() -> None:
    settings = load_settings()

    naming_service = NamingService(
        model=settings.text_model,
        client_id=settings.gigachat_client_id,
        authorization_key=settings.gigachat_authorization_key,
        scope=settings.gigachat_scope,
        base_url=settings.gigachat_base_url,
        auth_url=settings.gigachat_auth_url,
        verify_ssl=settings.gigachat_verify_ssl,
    )
    store = SQLiteStore(settings.sqlite_path)

    api_app = create_app(settings, store, naming_service)

    logger.info(
        "Starting bot (polling) and API on %s:%s", settings.api_host, settings.api_port
    )
    await asyncio.gather(
        _run_api(api_app, settings.api_host, settings.api_port),
        _run_bot(settings, naming_service, store),
    )


if __name__ == "__main__":
    asyncio.run(main())
