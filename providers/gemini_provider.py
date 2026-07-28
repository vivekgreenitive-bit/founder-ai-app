from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from providers.base_provider import BaseLLMProvider

class GeminiProvider(BaseLLMProvider):
    llm: Any
    api_key: str
    model: str
    temperature: float
    max_tokens: int

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", temperature: float = 0.1, max_tokens: int = 1000) -> None:
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=model,
            temperature=temperature,
            max_output_tokens=max_tokens
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
            self.llm.invoke("Hi")
            return True
        except Exception:
            return False

    def provider_name(self) -> str:
        return "gemini"
