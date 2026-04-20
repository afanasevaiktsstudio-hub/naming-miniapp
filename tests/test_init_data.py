import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from app.api.init_data import InitDataError, verify_init_data


BOT_TOKEN = "1234567890:AAAbbbCCCdddEEE"


def _sign(params: dict[str, str], bot_token: str = BOT_TOKEN) -> str:
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256
    ).digest()
    signature = hmac.new(
        secret_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    full = dict(params)
    full["hash"] = signature
    return urlencode(full)


def test_verify_init_data_happy_path() -> None:
    user = {"id": 42, "first_name": "Тест", "username": "user42"}
    params = {
        "auth_date": str(int(time.time())),
        "user": json.dumps(user, ensure_ascii=False),
        "query_id": "abc",
    }
    raw = _sign(params)
    data = verify_init_data(raw, BOT_TOKEN)
    assert data.user.id == 42
    assert data.user.first_name == "Тест"
    assert data.user.username == "user42"


def test_verify_init_data_invalid_signature() -> None:
    user = {"id": 7}
    params = {"auth_date": str(int(time.time())), "user": json.dumps(user)}
    raw = _sign(params, bot_token=BOT_TOKEN)
    bad = raw.replace("hash=", "hash=deadbeef&_orig=")
    with pytest.raises(InitDataError):
        verify_init_data(bad, BOT_TOKEN)


def test_verify_init_data_outdated() -> None:
    user = {"id": 7}
    params = {
        "auth_date": str(int(time.time()) - 24 * 60 * 60 - 10),
        "user": json.dumps(user),
    }
    raw = _sign(params)
    with pytest.raises(InitDataError):
        verify_init_data(raw, BOT_TOKEN, max_age_seconds=24 * 60 * 60)


def test_verify_init_data_missing_hash() -> None:
    raw = "auth_date=12345&user=%7B%22id%22%3A1%7D"
    with pytest.raises(InitDataError):
        verify_init_data(raw, BOT_TOKEN)


def test_verify_init_data_empty() -> None:
    with pytest.raises(InitDataError):
        verify_init_data("", BOT_TOKEN)
