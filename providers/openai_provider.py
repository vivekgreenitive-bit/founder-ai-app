from typing import Any
from langchain_openai import ChatOpenAI
from providers.base_provider import BaseLLMProvider

class OpenAIProvider(BaseLLMProvider):
    llm: Any
    api_key: str
    model: str
    temperature: float
    max_tokens: int

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", temperature: float = 0.1, max_tokens: int = 1000) -> None:
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.llm = ChatOpenAI(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def generate(self, prompt: str) -> str:
        return str(self.llm.invoke(prompt).content)

    def stream(self, prompt: str) -> Any:
        for chunk in self.llm.stream(prompt):
            yield chunk.content

    def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            # Lightweight prompt to verify API connectivity
            self.llm.invoke("Hi", max_completion_tokens=1)
            return True
        except Exception:
            return False

    def provider_name(self) -> str:
        return "openai"
