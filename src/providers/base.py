"""Abstract base class for all AI providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Message:
    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class ProviderResponse:
    content: str
    model: str
    provider: str
    usage: dict = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


class BaseProvider(ABC):
    """All AI providers must implement this interface."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    def complete(self, messages: List[Message], **kwargs) -> ProviderResponse:
        """Send messages and return a completion."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the provider is reachable and functional."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...
