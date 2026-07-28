from abc import ABC, abstractmethod
from typing import Any

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate response from prompt synchronously."""
        pass

    @abstractmethod
    def stream(self, prompt: str) -> Any:
        """Stream response generator from prompt."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verify provider availability and configuration."""
        pass

    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier."""
        pass
