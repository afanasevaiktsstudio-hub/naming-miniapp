import json
import re
import uuid

import httpx

from app.prompts.naming_prompt import SYSTEM_PROMPT


class NamingService:
    def __init__(
        self,
        model: str,
        client_id: str,
        authorization_key: str,
        scope: str,
        base_url: str,
        auth_url: str,
        verify_ssl: bool = True,
    ) -> None:
        self.model = model
        self.client_id = client_id
        self.authorization_key = authorization_key
        self.scope = scope
        self.base_url = base_url.rstrip("/")
        self.auth_url = auth_url
        self.verify_ssl = verify_ssl
        self._access_token: str | None = None

    async def generate(self, source_name: str) -> list[dict[str, str]]:
        token = await self._get_access_token()
        raw_content = await self._request_variants(token, source_name, strict=False)
        try:
            variants = self.parse_variants(raw_content)
        except Exception:
            # Retry once with stricter prompt if model returned malformed JSON.
            raw_content = await self._request_variants(token, source_name, strict=True)
            try:
                variants = self.parse_variants(raw_content)
            except Exception:
                # Last fallback: request pipe-delimited text and parse it.
                text_rows = await self._request_variants_text(token, source_name)
                variants = self._parse_pipe_rows(text_rows)
        if len(variants) < 5:
            # Top up with one more low-temperature pass.
            extra_rows = await self._request_variants_text(token, source_name)
            merged = variants + self._parse_pipe_rows(extra_rows)
            variants = self._normalize_candidates(merged)
        if len(variants) < 5:
            variants = self._pad_variants(source_name, variants)
        return variants[:5]

    async def _request_variants(self, token: str, source_name: str, strict: bool) -> str:
        strict_suffix = (
            "\nReturn ONLY minified valid JSON object. No markdown, no comments, no extra text."
            if strict
            else ""
        )
        payload = {
            "model": self.model,
            "temperature": 0.9 if not strict else 0.7,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT + strict_suffix},
                {"role": "user", "content": f"English name: {source_name}"},
            ],
        }

        async with httpx.AsyncClient(timeout=45.0, verify=self.verify_ssl) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )
            if response.status_code == 401:
                self._access_token = None
                refreshed_token = await self._get_access_token()
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {refreshed_token}"},
                    json=payload,
                )
            response.raise_for_status()
            data = response.json()

        return (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

    async def _request_variants_text(self, token: str, source_name: str) -> str:
        payload = {
            "model": self.model,
            "temperature": 0.5,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Generate exactly 5 lines. "
                        "Each line format: title | style | comment. "
                        "No numbering, no markdown, no extra text."
                    ),
                },
                {"role": "user", "content": f"English name: {source_name}"},
            ],
        }
        async with httpx.AsyncClient(timeout=45.0, verify=self.verify_ssl) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        return (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

    async def _get_access_token(self) -> str:
        if self._access_token:
            return self._access_token

        headers = {
            "Authorization": f"Basic {self.authorization_key}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        data = {"scope": self.scope}

        async with httpx.AsyncClient(timeout=30.0, verify=self.verify_ssl) as client:
            response = await client.post(self.auth_url, headers=headers, data=data)
            response.raise_for_status()
            body = response.json()
            token = body.get("access_token", "")

        if not token:
            raise ValueError("GigaChat auth succeeded but returned empty access_token")

        self._access_token = token
        return token

    @staticmethod
    def parse_variants(raw_content: str) -> list[dict[str, str]]:
        try:
            data = NamingService._safe_json_load(raw_content)
            candidates = data.get("variants", [])
            if not isinstance(candidates, list):
                raise ValueError("Invalid variants format")
            return NamingService._normalize_candidates(candidates)
        except Exception:
            # Salvage malformed JSON with regex extraction.
            pattern = re.compile(
                r'"title"\s*:\s*"(?P<title>.*?)"\s*,\s*"style"\s*:\s*"(?P<style>.*?)"\s*,\s*"comment"\s*:\s*"(?P<comment>.*?)"',
                re.DOTALL,
            )
            candidates: list[dict[str, str]] = []
            for m in pattern.finditer(raw_content):
                candidates.append(
                    {
                        "title": m.group("title"),
                        "style": m.group("style"),
                        "comment": m.group("comment"),
                    }
                )
            if not candidates:
                raise
            return NamingService._normalize_candidates(candidates)

    @staticmethod
    def _parse_pipe_rows(raw_text: str) -> list[dict[str, str]]:
        candidates: list[dict[str, str]] = []
        for line in raw_text.splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3:
                continue
            candidates.append(
                {"title": parts[0], "style": parts[1], "comment": "|".join(parts[2:]).strip()}
            )
        return NamingService._normalize_candidates(candidates)

    @staticmethod
    def _normalize_candidates(candidates: list[dict]) -> list[dict[str, str]]:
        unique: list[dict[str, str]] = []
        seen_titles: set[str] = set()
        for item in candidates:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "")).strip().replace("\n", " ")
            style = str(item.get("style", "")).strip().replace("\n", " ")
            comment = str(item.get("comment", "")).strip().replace("\n", " ")
            if not title:
                continue
            normalized = title.lower()
            if normalized in seen_titles:
                continue
            seen_titles.add(normalized)
            unique.append({"title": title[:60], "style": style[:80], "comment": comment[:180]})
            if len(unique) == 5:
                break
        return unique

    @staticmethod
    def _pad_variants(source_name: str, current: list[dict[str, str]]) -> list[dict[str, str]]:
        base = source_name.strip() or "Проект"
        fillers = [
            {"title": f"{base} Рус", "style": "нейтральный", "comment": "Лаконичный вариант с русским акцентом."},
            {"title": f"{base} Дом", "style": "маркетинговый", "comment": "Более теплый и понятный для аудитории."},
            {"title": f"{base} Квартал", "style": "девелоперский", "comment": "Подходит для формата жилого комплекса."},
            {"title": f"{base} Пространство", "style": "креативный", "comment": "Подчеркивает современный характер проекта."},
            {"title": f"{base} Парк", "style": "универсальный", "comment": "Удачный нейтральный бренд для ЖК."},
        ]
        merged = current + fillers
        return NamingService._normalize_candidates(merged)

    @staticmethod
    def _safe_json_load(raw_content: str) -> dict:
        raw = raw_content.strip()
        if not raw:
            raise ValueError("Empty model response")

        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Model response is not JSON object")
        candidate = raw[start : end + 1]

        # Repair malformed control characters that occasionally break JSON parsing.
        candidate = re.sub(r"[\x00-\x1F]", " ", candidate)
        return json.loads(candidate)
