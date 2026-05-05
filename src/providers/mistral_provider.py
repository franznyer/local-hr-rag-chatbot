"""Mistral AI provider implementation."""
import logging
from typing import List

from src.providers.base import BaseProvider, Message, ProviderResponse

logger = logging.getLogger(__name__)


class MistralProvider(BaseProvider):
    provider_name = "mistral"

    def __init__(self, model_name: str, api_key: str):
        super().__init__(model_name)
        try:
            from mistralai import Mistral
            self._client = Mistral(api_key=api_key)
        except ImportError:
            raise ImportError("Run: pip install mistralai")

    def complete(self, messages: List[Message], **kwargs) -> ProviderResponse:
        payload = [{"role": m.role, "content": m.content} for m in messages]
        try:
            response = self._client.chat.complete(
                model=self.model_name,
                messages=payload,
                temperature=kwargs.get("temperature", 0.1),
            )
            choice = response.choices[0]
            return ProviderResponse(
                content=choice.message.content,
                model=self.model_name,
                provider=self.provider_name,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                },
            )
        except Exception as exc:
            logger.error("Mistral error: %s", exc)
            return ProviderResponse(
                content="", model=self.model_name,
                provider=self.provider_name, error=str(exc),
            )

    def health_check(self) -> bool:
        try:
            self._client.models.list()
            return True
        except Exception:
            return False
