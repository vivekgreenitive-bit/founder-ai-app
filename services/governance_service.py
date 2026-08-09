"""
services/governance_service.py
Controls whether agentic financial actions (Circle USDC) are enabled.
Default: DISCONNECTED. Must be explicitly opted-in via Settings → Automation & Governance.
This gates the orchestrator's payment detection path.
"""
import json
import os
from typing import Any, Dict

GOVERNANCE_FILE = os.path.join("config", "governance.json")

_defaults: Dict[str, Any] = {
    "agentic_payments_enabled": False,
    "testnet_only": True,
    "max_transaction_limit": 200,
    "daily_limit": 500,
    "monthly_budget": 2000,
    "emergency_stop": False,
}


class GovernanceService:
    """
    Gate for all agentic financial actions.
    Orchestrator checks is_agentic_payments_enabled() before any Circle/payment flow.
    """

    def __init__(self, config_path: str = GOVERNANCE_FILE):
        self._path = config_path
        self._ensure_config()

    def _ensure_config(self) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        if not os.path.exists(self._path):
            self._save(dict(_defaults))

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self._path, "r") as f:
                data = json.load(f)
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
            print(f"[GovernanceService] Error saving governance config: {e}")

    # ── Public API ───────────────────────────────────────────────────────────

    def is_agentic_payments_enabled(self) -> bool:
        """
        Returns True ONLY when the founder has explicitly opted-in AND
        emergency stop is NOT active.
        """
        cfg = self._load()
        if cfg.get("emergency_stop", False):
            return False
        return bool(cfg.get("agentic_payments_enabled", False))

    def is_emergency_stop_active(self) -> bool:
        return bool(self._load().get("emergency_stop", False))

    def is_testnet_only(self) -> bool:
        return bool(self._load().get("testnet_only", True))

    def get_policy(self) -> Dict[str, Any]:
        return self._load()

    def enable_agentic_payments(self) -> None:
        cfg = self._load()
        cfg["agentic_payments_enabled"] = True
        self._save(cfg)

    def disable_agentic_payments(self) -> None:
        cfg = self._load()
        cfg["agentic_payments_enabled"] = False
        self._save(cfg)

    def activate_emergency_stop(self) -> None:
        cfg = self._load()
        cfg["emergency_stop"] = True
        self._save(cfg)

    def deactivate_emergency_stop(self) -> None:
        cfg = self._load()
        cfg["emergency_stop"] = False
        self._save(cfg)

    def update_limits(self, max_tx: float, daily: float, monthly: float) -> None:
        cfg = self._load()
        cfg["max_transaction_limit"] = max_tx
        cfg["daily_limit"] = daily
        cfg["monthly_budget"] = monthly
        self._save(cfg)
