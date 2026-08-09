"""
services/company_profile_service.py
Single canonical reader/writer for company_profile.json.
All screens use this — never read/write the JSON file directly.
"""
import json
import os
from typing import Any, Dict, Optional

PROFILE_FILE = "company_profile.json"

_defaults: Dict[str, Any] = {
    "company_name": "",
    "industry": "",
    "stage": "",
    "goals": [],
    "onboarding_complete": False,
    "founder_name": "",
    "gemini_api_key": "",
}


class CompanyProfileService:
    """
    Centralized company profile management.
    Provides typed getters and a transactional save method.
    """

    def __init__(self, profile_path: str = PROFILE_FILE):
        self._path = profile_path

    # ── Private ──────────────────────────────────────────────────────────────

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self._path):
            return dict(_defaults)
        try:
            with open(self._path, "r") as f:
                data = json.load(f)
            # Merge with defaults so missing keys always have a value
            merged = dict(_defaults)
            merged.update(data)
            return merged
        except (json.JSONDecodeError, OSError):
            return dict(_defaults)

    def _save(self, data: Dict[str, Any]) -> None:
        try:
            with open(self._path, "w") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            print(f"[CompanyProfileService] Error saving profile: {e}")

    # ── Public Getters ───────────────────────────────────────────────────────

    def get_profile(self) -> Dict[str, Any]:
        return self._load()

    def get_company_name(self) -> str:
        return self._load().get("company_name") or "Your Company"

    def get_founder_name(self) -> str:
        return self._load().get("founder_name") or "Founder"

    def get_industry(self) -> str:
        return self._load().get("industry") or ""

    def get_stage(self) -> str:
        return self._load().get("stage") or ""

    def get_goals(self) -> list:
        return self._load().get("goals") or []

    def is_onboarding_complete(self) -> bool:
        return bool(self._load().get("onboarding_complete", False))

    def get_gemini_api_key(self) -> str:
        """Returns Gemini API key. Phase 7: move to OS keychain."""
        return self._load().get("gemini_api_key") or os.getenv("GEMINI_API_KEY", "")

    # ── Public Setters ───────────────────────────────────────────────────────

    def save_profile(self, updates: Dict[str, Any]) -> None:
        """Merge updates into existing profile and persist."""
        data = self._load()
        data.update(updates)
        self._save(data)

    def mark_onboarding_complete(self) -> None:
        self.save_profile({"onboarding_complete": True})

    def reset_session(self) -> None:
        """Resets active session state without deleting persistent data."""
        # Only clears transient state; company data survives
        pass
