import os
import json
from typing import Dict, Any, List

SETTINGS_FILE = os.path.join("config", "subscription.json")

class EntitlementService:
    """
    Centralized Entitlement & Subscription Management Service.
    Controls Free vs Pro feature gating, framework entitlements, and usage limits.
    """
    FREE_FRAMEWORKS = ["ECG KISS", "SLR CAMERAS"]
    ALL_FRAMEWORKS = [
        "ECG KISS", "SLR CAMERAS", "MC BEERS", "PC PEERS", "PS ERP", "DC ERPRS",
        "OKS REC SME", "PFA SAAS SME", "RSS FEED SME", "RPM REAP ER", "RUN DCMS ER",
        "ERM FABS ER", "ADMINS ER"
    ]
    MONTHLY_FREE_DIAGNOSIS_LIMIT = 5

    def __init__(self, config_path: str = SETTINGS_FILE):
        self.config_path = config_path
        self._ensure_config_exists()

    def _ensure_config_exists(self) -> None:
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        if not os.path.exists(self.config_path):
            default_state = {
                "plan": "FREE",  # "FREE", "PRO", "TRIAL", "CANCELLED"
                "status": "active",
                "subscription_id": None,
                "renewal_date": None,
                "monthly_diagnoses_used": 0
            }
            self._save_state(default_state)

    def _load_state(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception:
            return {"plan": "FREE", "status": "active", "monthly_diagnoses_used": 0}

    def _save_state(self, state: Dict[str, Any]) -> None:
        try:
            with open(self.config_path, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Error saving subscription state: {e}")

    def get_current_plan(self) -> str:
        state = self._load_state()
        return state.get("plan", "FREE").upper()

    def get_user_plan(self) -> str:
        return self.get_current_plan()

    def is_pro(self) -> bool:
        return self.get_current_plan() in ["PRO", "ENTERPRISE", "TRIAL"]

    def is_enterprise(self) -> bool:
        return self.get_current_plan() == "ENTERPRISE"

    def upgrade_to_enterprise(self) -> None:
        state = self._load_state()
        state["plan"] = "ENTERPRISE"
        state["status"] = "active"
        self._save_state(state)

    def can_access_framework(self, framework_name: str) -> bool:
        if self.is_pro():
            return True
        return framework_name.upper() in [f.upper() for f in self.FREE_FRAMEWORKS]

    def can_use_customer_intel(self) -> bool:
        return self.is_pro()

    def can_use_cloud_llm(self) -> bool:
        return self.is_pro()

    def can_execute_agentic_payments(self) -> bool:
        return self.is_pro()

    def can_run_diagnosis(self) -> bool:
        if self.is_pro():
            return True
        state = self._load_state()
        used = state.get("monthly_diagnoses_used", 0)
        return used < self.MONTHLY_FREE_DIAGNOSIS_LIMIT

    def increment_diagnosis_usage(self) -> None:
        state = self._load_state()
        state["monthly_diagnoses_used"] = state.get("monthly_diagnoses_used", 0) + 1
        self._save_state(state)

    def activate_pro_subscription(self, subscription_id: str, renewal_date: str = None) -> None:
        state = self._load_state()
        state["plan"] = "PRO"
        state["status"] = "active"
        state["subscription_id"] = subscription_id
        state["renewal_date"] = renewal_date
        self._save_state(state)

    def cancel_subscription(self) -> None:
        state = self._load_state()
        state["plan"] = "FREE"
        state["status"] = "cancelled"
        self._save_state(state)
