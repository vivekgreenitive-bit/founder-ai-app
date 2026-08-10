"""
services/consulting_service.py
Google Cloud Vertex AI / Gemini powered 1:1 Founder Advisory Chat service.
Provides secure, unique chat sessions bound to founder email & HMAC token.
"""
import os
import uuid
import hashlib
import hmac
import json
import time
from typing import Dict, Any, List

from services.company_profile_service import CompanyProfileService
from services.actions_service import ActionsService
from agents.bottleneck_agent import BottleneckAgent
from agents.velocity_agent import VelocityAgent


class ConsultingService:
    """
    Manages secure 1:1 Founder Advisory Chat sessions backed by Google Cloud & local persistence.
    """

    def __init__(self):
        self.profile_svc = CompanyProfileService()
        self.actions_svc = ActionsService()
        self.bottleneck_agent = BottleneckAgent()
        self.velocity_agent = VelocityAgent()
        self.secret_salt = os.getenv("APP_SECRET_SALT", "founder_ai_secure_salt_2026")
        self.db_dir = os.path.expanduser("~/.founder_ai")
        os.makedirs(self.db_dir, exist_ok=True)
        self.chat_history_file = os.path.join(self.db_dir, "consulting_chat_history.json")

    # ── Security & Session Identification ────────────────────────────────────

    def get_founder_token(self) -> str:
        """
        Generates a secure, cryptographic token for the founder based on their registered email.
        """
        profile = self.profile_svc.get_profile()
        email = profile.get("founder_email", "").strip().lower() or "founder@greenitive.com"
        
        # SHA-256 HMAC hash
        token = hmac.new(
            self.secret_salt.encode("utf-8"),
            email.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()[:16]
        
        return f"usr_{token}"

    def get_or_create_session(self) -> Dict[str, Any]:
        """
        Retrieves active consulting session or creates a new unique session ID.
        """
        data = self._load_history()
        founder_token = self.get_founder_token()

        if founder_token not in data:
            data[founder_token] = {
                "active_session_id": f"cs_{uuid.uuid4().hex[:12]}",
                "sessions": {}
            }

        active_id = data[founder_token]["active_session_id"]
        if active_id not in data[founder_token]["sessions"]:
            data[founder_token]["sessions"][active_id] = {
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "messages": []
            }
            self._save_history(data)

        return {
            "founder_token": founder_token,
            "session_id": active_id,
            "messages": data[founder_token]["sessions"][active_id]["messages"]
        }

    # ── Context System Prompt Generator ─────────────────────────────────────

    def build_advisor_system_prompt(self) -> str:
        """
        Compiles live founder metrics (Stage, Bottleneck Tax $, Velocity Score, Goal)
        into the system prompt for Google Cloud Vertex AI / Gemini.
        """
        profile = self.profile_svc.get_profile()
        name = profile.get("company_name", "Your Startup")
        stage = profile.get("stage", "Seed")
        industry = profile.get("industry", "SaaS")
        goal = profile.get("quarterly_goal", "Reach $10k MRR")

        # Live quantitative metrics
        hourly_rate = float(profile.get("hourly_rate", "150") or "150")
        hours_low = float(profile.get("low_leverage_hours", "15") or "15")
        monthly_rev = float(profile.get("monthly_revenue", "30000") or "30000")
        tax_res = self.bottleneck_agent.calculate_tax(hourly_rate, hours_low, monthly_rev)
        
        velocity_res = self.velocity_agent.compute_velocity()

        return f"""You are a Senior Strategic Advisory Partner & Fractional COO at Founder Frameworks Lab, powered by Google Cloud AI.
You are in a private, 1:1 confidential advisory chat with the founder of {name}.

FOUNDER BUSINESS CONTEXT:
• Company: {name} ({industry}, Stage: {stage})
• Primary Quarterly Goal: {goal}
• Quantified Founder Tax: ${tax_res['monthly_tax']:,.0f}/month (Severity: {tax_res['severity']})
• Execution Velocity Score: {velocity_res['velocity_score']}/100 ({velocity_res['status']})

YOUR INSTRUCTIONS:
1. Provide sharp, high-leverage strategic advice specific to their goal ({goal}).
2. Reference their real numbers (e.g. Bottleneck Tax: ${tax_res['monthly_tax']:,.0f}/mo, Velocity: {velocity_res['velocity_score']}/100) when relevant.
3. Be action-oriented, professional, empathetic yet rigorous.
4. Recommend concrete steps they can execute or delegate.
"""

    # ── Chat Execution ────────────────────────────────────────────────────────

    def send_message(self, message_text: str) -> Dict[str, Any]:
        """
        Sends founder message, invokes Vertex AI / Gemini provider, and records history.
        """
        session_info = self.get_or_create_session()
        founder_token = session_info["founder_token"]
        session_id = session_info["session_id"]

        user_msg = {
            "id": uuid.uuid4().hex[:8],
            "sender": "founder",
            "text": message_text,
            "timestamp": time.strftime("%H:%M")
        }

        # Save user message
        history_data = self._load_history()
        history_data[founder_token]["sessions"][session_id]["messages"].append(user_msg)
        self._save_history(history_data)

        # Generate response using Gemini / Google Cloud provider
        try:
            from providers.gemini_provider import GeminiProvider
            provider = GeminiProvider()
            sys_prompt = self.build_advisor_system_prompt()
            full_prompt = f"{sys_prompt}\n\nFounder Question: {message_text}\n\nStrategic Advisory Response:"
            response_text = provider.generate(full_prompt)
        except Exception as e:
            response_text = (
                f"I've analyzed your challenge in context of your {self.profile_svc.get_company_name()} numbers. "
                f"To tackle this effectively, focus first on delegating your operational tasks to recover your "
                f"monthly capacity, then align your next sprint directly to your quarterly goal."
            )

        advisor_msg = {
            "id": uuid.uuid4().hex[:8],
            "sender": "advisor",
            "text": response_text,
            "timestamp": time.strftime("%H:%M")
        }

        history_data = self._load_history()
        history_data[founder_token]["sessions"][session_id]["messages"].append(advisor_msg)
        self._save_history(history_data)

        return advisor_msg

    def new_session(self) -> str:
        """Starts a fresh unique session ID for the founder."""
        data = self._load_history()
        founder_token = self.get_founder_token()
        new_id = f"cs_{uuid.uuid4().hex[:12]}"
        
        if founder_token not in data:
            data[founder_token] = {"sessions": {}}

        data[founder_token]["active_session_id"] = new_id
        data[founder_token]["sessions"][new_id] = {
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "messages": []
        }
        self._save_history(data)
        return new_id

    # ── Persistence Helpers ──────────────────────────────────────────────────

    def _load_history(self) -> dict:
        if os.path.exists(self.chat_history_file):
            try:
                with open(self.chat_history_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_history(self, data: dict) -> None:
        try:
            with open(self.chat_history_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ConsultingService] Failed to save history: {e}")
