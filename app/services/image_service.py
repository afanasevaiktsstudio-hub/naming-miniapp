import base64
import json

import httpx


class ImageService:
    def __init__(self, api_token: str, account_id: str, model: str) -> None:
        self.api_token = api_token
        self.account_id = account_id
        self.model = model

    async def generate(self, brand_name: str) -> bytes:
        safe_brand = " ".join(brand_name.split())[:48]
        primary_prompt = (
            f"Create a premium branding poster for the brand name '{safe_brand}'. "
            "Center composition, readable title text, abstract geometric emblem, "
            "soft gradient background, high contrast, modern corporate style, no people, no watermark."
        )
        nsfw_fallback_prompt = (
            "Create a safe neutral abstract branding poster with no sensitive content. "
            "Readable title text in center, geometric icon, gradient background, modern typography."
        )
        low_detail_fallback_prompt = (
            f"Create a colorful brand poster for '{safe_brand}'. "
            "Blue and cyan gradient background, sharp title typography, geometric symbol, "
            "balanced contrast, marketing visual style, no people, no watermark."
        )
        return await self._generate_with_fallback(
            primary_prompt,
            nsfw_fallback_prompt,
            low_detail_fallback_prompt,
        )

    async def _generate_with_fallback(
        self,
        prompt: str,
        nsfw_fallback_prompt: str,
        low_detail_fallback_prompt: str,
    ) -> bytes:
        try:
            image = await self._generate_once(prompt)
            if not self._looks_low_detail(image):
                return image
        except ValueError as exc:
            first_error = str(exc)
            if "code\": 3030" not in first_error and "NSFW" not in first_error:
                raise
            return await self._generate_once(nsfw_fallback_prompt)
        # Retry once if image is likely blank / too low-detail.
        return await self._generate_once(low_detail_fallback_prompt)

    @staticmethod
    def _looks_low_detail(image_bytes: bytes) -> bool:
        # Practical heuristic: near-empty white PNGs are often very small.
        return len(image_bytes) < 15_000

    async def _generate_once(self, prompt: str) -> bytes:
        url = (
            "https://api.cloudflare.com/client/v4/accounts/"
            f"{self.account_id}/ai/run/{self.model}"
        )
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={"prompt": prompt, "output_format": "png"},
            )
            if response.status_code >= 400:
                try:
                    payload = response.json()
                    details = json.dumps(payload, ensure_ascii=False)
                except Exception:
                    details = response.text
                raise ValueError(f"Cloudflare image generation failed: {details}")

            content_type = response.headers.get("content-type", "").lower()
            if content_type.startswith("image/"):
                return response.content

            payload = response.json()
            if payload.get("success") is False:
                details = json.dumps(payload, ensure_ascii=False)
                raise ValueError(f"Cloudflare returned success=false: {details}")

            result = payload.get("result")
            image_ref = ""
            if isinstance(result, dict):
                image_ref = str(
                    result.get("image")
                    or result.get("b64_json")
                    or result.get("output")
                    or ""
                )
            elif isinstance(result, str):
                image_ref = result
            if not image_ref:
                details = json.dumps(payload, ensure_ascii=False)
                raise ValueError(f"Cloudflare response has no image field: {details}")

            if image_ref.startswith("http://") or image_ref.startswith("https://"):
                image_response = await client.get(image_ref)
                image_response.raise_for_status()
                return image_response.content
            if image_ref.startswith("data:"):
                _, _, image_ref = image_ref.partition(",")
            try:
                return base64.b64decode(image_ref, validate=False)
            except Exception as exc:  # noqa: BLE001
                raise ValueError("Failed to decode Cloudflare base64 image") from exc
