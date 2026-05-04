"""Anthropic Claude provider implementation."""
import logging
from typing import List

from src.providers.base import BaseProvider, Message, ProviderResponse

logger = logging.getLogger(__name__)


class ClaudeProvider(BaseProvider):
    provider_name = "claude"

    def __init__(self, model_name: str, api_key: str):
        super().__init__(model_name)
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("Run: pip install anthropic")

    def complete(self, messages: List[Message], **kwargs) -> ProviderResponse:
        system_prompt = ""
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        try:
            response = self._client.messages.create(
                model=self.model_name,
                max_tokens=kwargs.get("max_tokens", 2048),
                system=system_prompt,
                messages=chat_messages,
                temperature=kwargs.get("temperature", 0.1),
            )
            return ProviderResponse(
                content=response.content[0].text,
                model=self.model_name,
                provider=self.provider_name,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            )
        except Exception as exc:
            logger.error("Claude error: %s", exc)
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
