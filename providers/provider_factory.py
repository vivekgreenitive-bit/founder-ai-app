import os
import json
from typing import Dict, Any
from providers.base_provider import BaseLLMProvider
from providers.local_provider import LocalProvider
from providers.openai_provider import OpenAIProvider
from providers.gemini_provider import GeminiProvider
from config import settings as global_settings

SETTINGS_FILE = os.path.join("config", "settings.json")

class ProviderFactory:
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Loads model settings configuration from file with defaults."""
        default_config = {
            "provider": "local",
            "local": {
                "model": "Llama-3.2-3B"
            },
            "openai": {
                "api_key": "",
                "model": "gpt-4o-mini"
            },
            "gemini": {
                "api_key": "",
                "model": "gemini-1.5-flash"
            }
        }
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    user_config = json.load(f)
                    # Deep merge dicts to ensure structure
                    for key, val in user_config.items():
                        if isinstance(val, dict) and key in default_config:
                            default_config[key].update(val)
                        else:
                            default_config[key] = val
            except Exception as e:
                print(f"Error loading settings.json: {e}")
        return default_config

    @staticmethod
    def save_config(config: Dict[str, Any]) -> None:
        """Saves model settings configuration back to file."""
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving settings.json: {e}")

    @staticmethod
    def create(config: Dict[str, Any] = None) -> BaseLLMProvider:
        """Instantiates the correct LLM provider, applying environment overrides if present."""
        if config is None:
            config = ProviderFactory.load_config()

        provider_type = config.get("provider", "local").lower()
        
        # Read parameters from global settings
        temperature = global_settings.llm_temperature
        max_tokens = global_settings.llm_max_tokens
        n_ctx = global_settings.llm_n_ctx
        model_path = global_settings.model_path

        if provider_type == "openai":
            api_key = os.getenv("OPENAI_API_KEY", config.get("openai", {}).get("api_key", ""))
            model = os.getenv("OPENAI_MODEL_NAME", config.get("openai", {}).get("model", "gpt-4o-mini"))
            if not api_key:
                print("OpenAI API key missing. Falling back to Local model.")
                return LocalProvider(model_path, temperature, max_tokens, n_ctx)
            return OpenAIProvider(api_key, model, temperature, max_tokens)

        elif provider_type == "gemini":
            api_key = os.getenv("GEMINI_API_KEY", config.get("gemini", {}).get("api_key", ""))
            model = os.getenv("GEMINI_MODEL_NAME", config.get("gemini", {}).get("model", "gemini-1.5-flash"))
            if not api_key:
                print("Gemini API key missing. Falling back to Local model.")
                return LocalProvider(model_path, temperature, max_tokens, n_ctx)
            return GeminiProvider(api_key, model, temperature, max_tokens)

        else: # local
            return LocalProvider(model_path, temperature, max_tokens, n_ctx)
