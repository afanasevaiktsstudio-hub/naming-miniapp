"""Проверка поведения NamingService._post_chat при истёкшем access_token.

Симулируем GigaChat через httpx.MockTransport: первый чат-запрос — 401,
OAuth — 200 с новым токеном, повторный чат-запрос — 200.
"""
from __future__ import annotations

import json

import httpx
import pytest

from app.services.naming_service import NamingService


def _chat_body(text: str) -> dict:
    return {
        "choices": [
            {"message": {"content": text, "role": "assistant"}},
        ]
    }


class _Scenario:
    def __init__(self) -> None:
        self.chat_calls = 0
        self.oauth_calls = 0
        self.last_authorizations: list[str] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        if "oauth" in request.url.path:
            self.oauth_calls += 1
            return httpx.Response(
                200,
                json={"access_token": f"fresh-{self.oauth_calls}", "expires_at": 0},
            )
        if request.url.path.endswith("/chat/completions"):
            self.chat_calls += 1
            self.last_authorizations.append(request.headers.get("authorization", ""))
            if self.chat_calls == 1:
                return httpx.Response(401, json={"error": "expired"})
            return httpx.Response(200, json=_chat_body("{\"variants\": []}"))
        return httpx.Response(404)


@pytest.fixture()
def naming_service() -> NamingService:
    svc = NamingService(
        model="GigaChat-2-Pro",
        client_id="cid",
        authorization_key="auth",
        scope="GIGACHAT_API_PERS",
        base_url="https://example.test/api/v1",
        auth_url="https://example.test/oauth",
        verify_ssl=False,
    )
    # Pretend we already have a cached (stale) token.
    svc._access_token = "stale-token"
    return svc


@pytest.mark.asyncio
async def test_post_chat_retries_once_on_401(
    monkeypatch: pytest.MonkeyPatch, naming_service: NamingService
) -> None:
    scenario = _Scenario()
    transport = httpx.MockTransport(scenario.handle)

    real_client = httpx.AsyncClient

    def patched_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(
        "app.services.naming_service.httpx.AsyncClient", patched_client
    )

    result = await naming_service._post_chat({"model": "x", "messages": []})

    assert result == '{"variants": []}'
    assert scenario.chat_calls == 2, "expected exactly one retry after 401"
    assert scenario.oauth_calls == 1, "expected one token refresh"
    assert scenario.last_authorizations[0] == "Bearer stale-token"
    assert scenario.last_authorizations[1] == "Bearer fresh-1"
    assert naming_service._access_token == "fresh-1"


@pytest.mark.asyncio
async def test_post_chat_propagates_second_401(
    monkeypatch: pytest.MonkeyPatch, naming_service: NamingService
) -> None:
    calls = {"chat": 0, "oauth": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth" in request.url.path:
            calls["oauth"] += 1
            return httpx.Response(200, json={"access_token": "fresh", "expires_at": 0})
        calls["chat"] += 1
        return httpx.Response(401, json={"error": "still broken"})

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient

    def patched_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(
        "app.services.naming_service.httpx.AsyncClient", patched_client
    )

    with pytest.raises(httpx.HTTPStatusError):
        await naming_service._post_chat({"model": "x", "messages": []})

    assert calls["chat"] == 2
    assert calls["oauth"] == 1


# Keep "json" import used if assertions ever need it.
_ = json
