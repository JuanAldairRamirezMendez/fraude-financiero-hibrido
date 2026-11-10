from __future__ import annotations

from typing import Any

import httpx

from app.core.errors import ServiceUnavailableError
from app.core.settings import Settings
from app.schemas.api import ChatRequest


class GeminiChatService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def reply(self, payload: ChatRequest) -> str:
        api_key = self.settings.gemini_api_key
        if not api_key:
            raise ServiceUnavailableError(
                "El asistente de IA no está configurado. Añade GEMINI_API_KEY al servicio."
            )

        contents: list[dict[str, Any]] = [
            {"role": item.role, "parts": [{"text": item.content}]} for item in payload.history
        ]
        contents.append({"role": "user", "parts": [{"text": payload.message}]})
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.gemini_model}:generateContent"
        )
        body = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "Eres SentinelAI Copilot, un asistente para analistas de fraude. "
                            "Responde en español, con precisión y brevedad. Explica señales, "
                            "riesgos y próximos pasos; no inventes datos del dashboard ni "
                            "asegures que una transacción es fraude sin evidencia."
                        )
                    }
                ]
            },
            "contents": contents,
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 700},
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.gemini_timeout_seconds) as client:
                response = await client.post(url, params={"key": api_key}, json=body)
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise ServiceUnavailableError(
                "Gemini no está disponible en este momento. Inténtalo de nuevo."
            ) from error

        data = response.json()
        text = self._extract_text(data)
        if not text:
            raise ServiceUnavailableError("Gemini no devolvió una respuesta utilizable.")
        return text

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "\n".join(
            str(part["text"]).strip() for part in parts if isinstance(part, dict) and part.get("text")
        ).strip()