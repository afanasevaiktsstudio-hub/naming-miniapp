import json
import re
import uuid

import httpx

from app.prompts.naming_prompt import SYSTEM_PROMPT


_LATIN_RE = re.compile(r"[A-Za-z]")
_CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
_JSON_JUNK_CHARS = "{}[],"


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
        """Generate 5 Russified naming variants.

        Guarantees: resulting list has exactly 5 items, no Latin letters
        in any title, no JSON artifacts in fields. If GigaChat responds
        with English names or malformed output we perform up to one
        strict re-request and a pipe-text fallback before padding.
        """
        variants = await self._try_json(source_name, strict=False)

        if len(variants) < 5:
            stricter = await self._try_json(source_name, strict=True)
            variants = self._merge_unique(variants, stricter)

        if len(variants) < 5:
            try:
                text_rows = await self._request_variants_text(source_name)
                variants = self._merge_unique(
                    variants, self._parse_pipe_rows(text_rows)
                )
            except Exception:
                pass

        if len(variants) < 5:
            variants = self._pad_variants(source_name, variants)

        return variants[:5]

    async def _try_json(self, source_name: str, strict: bool) -> list[dict[str, str]]:
        try:
            raw = await self._request_variants(source_name, strict=strict)
        except Exception:
            return []
        try:
            return self.parse_variants(raw)
        except Exception:
            return []

    async def _post_chat(self, payload: dict) -> str:
        """POST to /chat/completions with a single retry on 401.

        GigaChat access tokens have a short TTL (~30 minutes). The cached token
        may look valid on our side but already be rejected by the server.
        On 401 we drop the cache, refresh and retry the exact same payload once.
        """
        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=45.0, verify=self.verify_ssl) as client:
            token = await self._get_access_token()
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )
            if response.status_code == 401:
                self._access_token = None
                refreshed = await self._get_access_token()
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {refreshed}"},
                    json=payload,
                )
            response.raise_for_status()
            data = response.json()
        return (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

    async def _request_variants(self, source_name: str, strict: bool) -> str:
        strict_suffix = (
            "\n\nВАЖНО: предыдущий ответ содержал латиницу или мусор. "
            "Верни ТОЛЬКО минифицированный JSON-объект. Все поля — ТОЛЬКО "
            "на русском (кириллица). Ни одной латинской буквы. Никаких "
            "markdown, комментариев или пояснений до/после JSON."
            if strict
            else ""
        )
        payload = {
            "model": self.model,
            "temperature": 0.7 if strict else 0.9,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT + strict_suffix},
                {
                    "role": "user",
                    "content": (
                        f"Рабочее англоязычное название: {source_name}. "
                        "Сгенерируй 5 русифицированных вариантов согласно системным правилам."
                    ),
                },
            ],
        }
        return await self._post_chat(payload)

    async def _request_variants_text(self, source_name: str) -> str:
        payload = {
            "model": self.model,
            "temperature": 0.5,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Сгенерируй ровно 5 строк. Только кириллица, никакой "
                        "латиницы. Формат каждой строки: "
                        "title | style | comment. "
                        "title — русифицированное название (1–6 слов, без "
                        "латинских букв). "
                        "style — один из: буквальный, нейтрально-маркетинговый, "
                        "креативный, короткий и звучный, смелый/необычный. "
                        "comment — короткий русский комментарий. "
                        "Без нумерации, markdown, JSON и прочего лишнего текста."
                    ),
                },
                {"role": "user", "content": f"Англоязычное название: {source_name}"},
            ],
        }
        return await self._post_chat(payload)

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
                {
                    "title": parts[0],
                    "style": parts[1],
                    "comment": "|".join(parts[2:]).strip(),
                }
            )
        return NamingService._normalize_candidates(candidates)

    @staticmethod
    def _clean_field(value: str) -> str:
        """Strip JSON artifacts (`}, {`, trailing brackets) and whitespace."""
        s = str(value).strip().replace("\n", " ").replace("\r", " ")
        s = re.sub(r"\s+", " ", s)
        while s and s[-1] in _JSON_JUNK_CHARS:
            s = s[:-1].rstrip()
        while s and s[0] in _JSON_JUNK_CHARS:
            s = s[1:].lstrip()
        return s

    @staticmethod
    def _is_russian_title(title: str) -> bool:
        """Title is acceptable if it has Cyrillic letters and no Latin ones."""
        if not title:
            return False
        if _LATIN_RE.search(title):
            return False
        if not _CYRILLIC_RE.search(title):
            return False
        return True

    @staticmethod
    def _normalize_candidates(candidates: list[dict]) -> list[dict[str, str]]:
        """Deduplicate, clean JSON noise, reject variants with Latin titles."""
        unique: list[dict[str, str]] = []
        seen_titles: set[str] = set()
        for item in candidates:
            if not isinstance(item, dict):
                continue
            title = NamingService._clean_field(item.get("title", ""))
            style = NamingService._clean_field(item.get("style", ""))
            comment = NamingService._clean_field(item.get("comment", ""))

            if not NamingService._is_russian_title(title):
                continue

            normalized = title.lower()
            if normalized in seen_titles:
                continue
            seen_titles.add(normalized)
            unique.append(
                {
                    "title": title[:60],
                    "style": style[:80],
                    "comment": comment[:180],
                }
            )
            if len(unique) == 5:
                break
        return unique

    @staticmethod
    def _merge_unique(
        primary: list[dict[str, str]], extra: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        seen = {v["title"].lower() for v in primary}
        merged = list(primary)
        for item in extra:
            key = item.get("title", "").lower()
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(item)
            if len(merged) == 5:
                break
        return merged

    @staticmethod
    def _pad_variants(
        source_name: str, current: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        """Last-resort filler. Uses neutral Russian words, never the source."""
        fillers = [
            {
                "title": "Русский Квартал",
                "style": "нейтрально-маркетинговый",
                "comment": "Страховочный вариант: подходит любому ЖК.",
            },
            {
                "title": "Отечественный Двор",
                "style": "буквальный",
                "comment": "Подчёркивает идею «по-отечественному».",
            },
            {
                "title": "Радушный Дом",
                "style": "короткий и звучный",
                "comment": "Тёплое, понятное имя без иностранщины.",
            },
            {
                "title": "Своё Пространство",
                "style": "креативный",
                "comment": "Игра на «своё, родное».",
            },
            {
                "title": "Дубовая Слобода",
                "style": "смелый/необычный",
                "comment": "Плотный русский образ на случай пустого ответа.",
            },
        ]
        _ = source_name
        return NamingService._merge_unique(current, fillers)

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

        candidate = re.sub(r"[\x00-\x1F]", " ", candidate)
        return json.loads(candidate)
