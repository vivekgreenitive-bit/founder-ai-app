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

    def invoke(self, prompt: Any, stop: Any = None, **kwargs: Any) -> str:
        """Compatibility wrapper for LangChain Runnable interface."""
        return self.generate(str(prompt))

    def analyze_customer_profile(self, business_description: str) -> dict:
        """Analyze business description and produce structured customer intelligence persona & competition."""
        prompt = f"""You are a startup strategy analyst. Given the business description below, produce:
1. A primary customer persona (demographics, pain points, buying triggers)
2. 3 likely direct competitors with a one-line positioning note on each
3. One clear differentiation opportunity based on the gap between the persona's needs and competitor offerings

Business description: {business_description}

Respond ONLY in valid JSON format matching this exact structure:
{{
  "persona": {{"name": "...", "demographics": "...", "pain_points": ["..."], "buying_triggers": ["..."]}},
  "competitors": [{{"name": "...", "positioning": "..."}}],
  "differentiation_opportunity": "...",
  "recommended_framework": "..."
}}"""
        res = self.generate(prompt)
        import json, re
        match = re.search(r"\{.*\}", res, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        return {
            "persona": {"name": "Target Founder", "demographics": "B2B SMBs", "pain_points": ["Operations overload"], "buying_triggers": ["Scalability bottlenecks"]},
            "competitors": [{"name": "Generic Advisory", "positioning": "Manual & Expensive"}],
            "differentiation_opportunity": "AI-native execution grounded in proven operating frameworks.",
            "recommended_framework": "RUN DCMS ER"
        }
