import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    text_provider: str
    text_model: str
    gigachat_client_id: str
    gigachat_authorization_key: str
    gigachat_scope: str
    gigachat_base_url: str
    gigachat_auth_url: str
    gigachat_verify_ssl: bool
    cloudflare_api_token: str
    cloudflare_account_id: str
    cloudflare_image_model: str
    sqlite_path: str
    max_input_length: int
    daily_text_limit: int
    daily_image_limit: int
    miniapp_url: str
    api_host: str
    api_port: int
    api_cors_origins: tuple[str, ...]
    debug_user_id: int


def _read_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    text_provider = os.getenv("TEXT_PROVIDER", "gigachat").strip().lower()
    text_model = os.getenv("TEXT_MODEL", "GigaChat-2-Pro").strip()
    gigachat_client_id = os.getenv("GIGACHAT_CLIENT_ID", "").strip()
    gigachat_authorization_key = os.getenv("GIGACHAT_AUTHORIZATION_KEY", "").strip()
    gigachat_scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS").strip()
    gigachat_base_url = os.getenv(
        "GIGACHAT_BASE_URL", "https://gigachat.devices.sberbank.ru/api/v1"
    ).strip()
    gigachat_auth_url = os.getenv(
        "GIGACHAT_AUTH_URL", "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    ).strip()
    gigachat_verify_ssl = _read_bool("GIGACHAT_VERIFY_SSL", True)
    cloudflare_api_token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    cloudflare_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    cloudflare_image_model = os.getenv(
        "CLOUDFLARE_IMAGE_MODEL", "@cf/black-forest-labs/flux-1-schnell"
    ).strip()
    sqlite_path = os.getenv("SQLITE_PATH", "bot.db").strip()
    max_input_length = int(os.getenv("MAX_INPUT_LENGTH", "120"))
    daily_text_limit = int(os.getenv("DAILY_TEXT_LIMIT", "20"))
    daily_image_limit = int(os.getenv("DAILY_IMAGE_LIMIT", "5"))
    miniapp_url = os.getenv("MINIAPP_URL", "").strip()
    api_host = os.getenv("API_HOST", "0.0.0.0").strip()
    api_port = int(os.getenv("API_PORT", "8080"))
    cors_raw = os.getenv("API_CORS_ORIGINS", "").strip()
    api_cors_origins = tuple(
        origin.strip() for origin in cors_raw.split(",") if origin.strip()
    )
    debug_user_id = int(os.getenv("DEBUG_USER_ID", "0"))

    if not bot_token:
        raise ValueError("BOT_TOKEN is missing. Put it in .env")
    if text_provider != "gigachat":
        raise ValueError("Only TEXT_PROVIDER=gigachat is supported in this MVP")
    if not gigachat_client_id:
        raise ValueError("GIGACHAT_CLIENT_ID is missing. Put it in .env")
    if not gigachat_authorization_key:
        raise ValueError("GIGACHAT_AUTHORIZATION_KEY is missing. Put it in .env")

    return Settings(
        bot_token=bot_token,
        text_provider=text_provider,
        text_model=text_model,
        gigachat_client_id=gigachat_client_id,
        gigachat_authorization_key=gigachat_authorization_key,
        gigachat_scope=gigachat_scope,
        gigachat_base_url=gigachat_base_url,
        gigachat_auth_url=gigachat_auth_url,
        gigachat_verify_ssl=gigachat_verify_ssl,
        cloudflare_api_token=cloudflare_api_token,
        cloudflare_account_id=cloudflare_account_id,
        cloudflare_image_model=cloudflare_image_model,
        sqlite_path=sqlite_path,
        max_input_length=max_input_length,
        daily_text_limit=daily_text_limit,
        daily_image_limit=daily_image_limit,
        miniapp_url=miniapp_url,
        api_host=api_host,
        api_port=api_port,
        api_cors_origins=api_cors_origins,
        debug_user_id=debug_user_id,
    )
