import os
from typing import Any
from langchain_community.llms import LlamaCpp
from providers.base_provider import BaseLLMProvider
from config import settings

class LocalProvider(BaseLLMProvider):
    llm: Any

    def __init__(self, model_path: str, temperature: float, max_tokens: int, n_ctx: int) -> None:
        self.model_path = model_path
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.n_ctx = n_ctx
        self.llm = None
        self._init_model()

    def _init_model(self) -> None:
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Local model not found at: {self.model_path}")
        
        import multiprocessing
        threads = max(1, multiprocessing.cpu_count() // 2)
        
        self.llm = LlamaCpp(
            model_path=self.model_path,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            n_ctx=self.n_ctx,
            n_threads=threads,
            stop=["<|eot_id|>", "Context:", "Question:"],
            verbose=False
        )

    def generate(self, prompt: str) -> str:
        if not self.llm:
            self._init_model()
        return self.llm.invoke(prompt)

    def stream(self, prompt: str) -> Any:
        if not self.llm:
            self._init_model()
        return self.llm.stream(prompt)

    def health_check(self) -> bool:
        return os.path.exists(self.model_path) and self.llm is not None

    def provider_name(self) -> str:
        return "local"
