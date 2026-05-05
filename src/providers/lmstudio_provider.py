"""LM Studio provider — uses OpenAI-compatible API (100% local)."""
import logging
from typing import List

import requests

from src.providers.base import BaseProvider, Message, ProviderResponse

logger = logging.getLogger(__name__)


class LMStudioProvider(BaseProvider):
    provider_name = "lmstudio"

    def __init__(self, model_name: str, base_url: str):
        super().__init__(model_name)
        self._base_url = base_url.rstrip("/")

    def complete(self, messages: List[Message], **kwargs) -> ProviderResponse:
        payload = {
            "model": self.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.1),
        }
        try:
            resp = requests.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            return ProviderResponse(
                content=choice["message"]["content"],
                model=data.get("model", self.model_name),
                provider=self.provider_name,
                usage=data.get("usage", {}),
            )
        except Exception as exc:
            logger.error("LM Studio error: %s", exc)
            return ProviderResponse(
                content="", model=self.model_name,
                provider=self.provider_name, error=str(exc),
            )

    def health_check(self) -> bool:
        try:
            resp = requests.get(f"{self._base_url}/models", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
