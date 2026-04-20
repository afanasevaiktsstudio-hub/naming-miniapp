"""Валидация Telegram `initData` по HMAC.

Алгоритм из официальной документации Telegram WebApp:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl


@dataclass(frozen=True)
class InitDataUser:
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None


@dataclass(frozen=True)
class InitData:
    user: InitDataUser
    auth_date: int
    raw: str


class InitDataError(Exception):
    """Raised when initData payload is invalid, expired or tampered with."""


def _secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()


def verify_init_data(
    raw_init_data: str,
    bot_token: str,
    *,
    max_age_seconds: int = 24 * 60 * 60,
) -> InitData:
    """Проверить `initData` и вернуть структуру пользователя.

    Raises:
        InitDataError: если отсутствуют поля, подпись не сходится или данные протухли.
    """
    if not raw_init_data:
        raise InitDataError("initData is empty")

    parsed = dict(parse_qsl(raw_init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise InitDataError("hash is missing")

    # signature = HMAC_SHA256(data_check_string, secret_key)
    # где data_check_string — отсортированные по ключу пары "key=value",
    # соединённые переводами строки.
    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(parsed.items())
    )
    digest = hmac.new(
        _secret_key(bot_token),
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(digest, received_hash):
        raise InitDataError("hash mismatch")

    auth_date_raw = parsed.get("auth_date", "0")
    try:
        auth_date = int(auth_date_raw)
    except ValueError as exc:
        raise InitDataError("auth_date is not an integer") from exc

    if max_age_seconds > 0 and auth_date > 0:
        if time.time() - auth_date > max_age_seconds:
            raise InitDataError("initData is outdated")

    user_payload_raw = parsed.get("user")
    if not user_payload_raw:
        raise InitDataError("user is missing")
    try:
        user_payload: dict[str, Any] = json.loads(user_payload_raw)
    except json.JSONDecodeError as exc:
        raise InitDataError("user payload is not valid JSON") from exc

    user_id = user_payload.get("id")
    if not isinstance(user_id, int):
        raise InitDataError("user.id is missing or invalid")

    return InitData(
        user=InitDataUser(
            id=user_id,
            first_name=user_payload.get("first_name"),
            last_name=user_payload.get("last_name"),
            username=user_payload.get("username"),
            language_code=user_payload.get("language_code"),
        ),
        auth_date=auth_date,
        raw=raw_init_data,
    )
