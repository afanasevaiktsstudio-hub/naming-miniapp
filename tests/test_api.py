import hashlib
import hmac
import json
import tempfile
import time
from pathlib import Path
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient

from app.api.server import create_app
from app.config import Settings
from app.storage.sqlite_store import SQLiteStore


BOT_TOKEN = "1234567890:TESTTESTTESTTEST"


class FakeNaming:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def generate(self, source_name: str) -> list[dict[str, str]]:
        self.calls.append(source_name)
        return [
            {"title": f"{source_name}-{i}", "style": "стиль", "comment": "коммент"}
            for i in range(1, 6)
        ]


def _make_settings(tmp_path: Path) -> Settings:
    return Settings(
        bot_token=BOT_TOKEN,
        text_provider="gigachat",
        text_model="GigaChat-2-Pro",
        gigachat_client_id="x",
        gigachat_authorization_key="x",
        gigachat_scope="x",
        gigachat_base_url="https://example",
        gigachat_auth_url="https://example/auth",
        gigachat_verify_ssl=False,
        cloudflare_api_token="",
        cloudflare_account_id="",
        cloudflare_image_model="",
        sqlite_path=str(tmp_path / "test.db"),
        max_input_length=64,
        daily_text_limit=3,
        daily_image_limit=0,
        miniapp_url="https://example.com",
        api_host="127.0.0.1",
        api_port=8080,
        api_cors_origins=("https://example.com",),
        debug_user_id=0,
    )


def _sign_init_data(user_id: int = 99) -> str:
    params = {
        "auth_date": str(int(time.time())),
        "user": json.dumps({"id": user_id, "first_name": "tester"}),
    }
    check = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    sig = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode({**params, "hash": sig})


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    settings = _make_settings(tmp_path)
    store = SQLiteStore(settings.sqlite_path)
    app = create_app(settings, store, FakeNaming())  # type: ignore[arg-type]
    return TestClient(app)


def test_health(client: TestClient) -> None:
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_requires_init_data(client: TestClient) -> None:
    res = client.get("/api/session")
    assert res.status_code == 401


def test_full_flow(client: TestClient) -> None:
    init = _sign_init_data(123)
    headers = {"X-Telegram-Init-Data": init}

    # пустая сессия
    res = client.get("/api/session", headers=headers)
    assert res.status_code == 200
    assert res.json() == {"source_name": None, "variants": [], "selected_index": None}

    # генерация вариантов
    res = client.post(
        "/api/variants",
        json={"source_name": "Riverside"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["variants"]) == 5
    assert data["session"]["source_name"] == "Riverside"

    # выбор варианта
    res = client.post("/api/select", json={"index": 2}, headers=headers)
    assert res.status_code == 200
    assert res.json()["selected_index"] == 2


def test_rate_limit(client: TestClient) -> None:
    init = _sign_init_data(555)
    headers = {"X-Telegram-Init-Data": init}
    for _ in range(3):
        r = client.post("/api/variants", json={"source_name": "X"}, headers=headers)
        assert r.status_code == 200
    r = client.post("/api/variants", json={"source_name": "Y"}, headers=headers)
    assert r.status_code == 429


def test_debug_user_header(tmp_path: Path) -> None:
    settings = Settings(**{**_make_settings(tmp_path).__dict__, "debug_user_id": 777})
    store = SQLiteStore(settings.sqlite_path)
    app = create_app(settings, store, FakeNaming())  # type: ignore[arg-type]
    with TestClient(app) as client:
        res = client.get("/api/session", headers={"X-Debug-User": "1"})
        assert res.status_code == 200


def test_select_without_variants(client: TestClient) -> None:
    init = _sign_init_data(321)
    headers = {"X-Telegram-Init-Data": init}
    res = client.post("/api/select", json={"index": 0}, headers=headers)
    assert res.status_code == 404


# Cleanup db file used in _make_settings happens via tmp_path fixture.
_ = tempfile  # silence "imported but unused" if tempfile import is ever removed
