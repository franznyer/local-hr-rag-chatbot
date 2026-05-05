"""Ollama provider implementation (100% local)."""
import logging
from typing import List

import requests

from src.providers.base import BaseProvider, Message, ProviderResponse

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    provider_name = "ollama"

    def __init__(self, model_name: str, base_url: str):
        super().__init__(model_name)
        self._base_url = base_url.rstrip("/")

    def complete(self, messages: List[Message], **kwargs) -> ProviderResponse:
        payload = {
            "model": self.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": kwargs.get("temperature", 0.1)},
        }
        try:
            resp = requests.post(
                f"{self._base_url}/api/chat",
                json=payload,
                timeout=120,
            )

            # Detect model-not-found before raising generically
            if resp.status_code == 404:
                body = resp.json()
                raw_error = body.get("error", "")
                if "not found" in raw_error.lower() or "try pulling" in raw_error.lower():
                    return ProviderResponse(
                        content="",
                        model=self.model_name,
                        provider=self.provider_name,
                        error=(
                            f"Modèle '{self.model_name}' introuvable dans Ollama. "
                            f"Lancez : ollama pull {self.model_name}"
                        ),
                    )

            resp.raise_for_status()
            data = resp.json()
            return ProviderResponse(
                content=data["message"]["content"],
                model=self.model_name,
                provider=self.provider_name,
                usage={
                    "prompt_eval_count": data.get("prompt_eval_count", 0),
                    "eval_count": data.get("eval_count", 0),
                },
            )

        except requests.exceptions.ConnectionError:
            return ProviderResponse(
                content="",
                model=self.model_name,
                provider=self.provider_name,
                error=(
                    f"Impossible de joindre Ollama sur {self._base_url}. "
                    "Vérifiez qu'il est lancé : ollama serve"
                ),
            )
        except Exception as exc:
            logger.error("Ollama error: %s", exc)
            return ProviderResponse(
                content="", model=self.model_name,
                provider=self.provider_name, error=str(exc),
            )

    def health_check(self) -> bool:
        try:
            resp = requests.get(f"{self._base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def list_local_models(self) -> List[str]:
        """Return names of models already pulled in Ollama."""
        try:
            resp = requests.get(f"{self._base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            return []
