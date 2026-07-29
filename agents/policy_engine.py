from typing import Tuple, Dict, Any
from db.payment_db import PaymentDBManager

class PolicyEngine:
    def __init__(self, db_manager: PaymentDBManager):
        self.db = db_manager

    def evaluate(self, amount: float, merchant: str, category: str) -> Tuple[bool, str]:
        """
        Evaluates a proposed payment against the active signed policies.
        Returns (is_allowed, reason).
        """
        policy = self.db.get_active_policy()
        if not policy:
            return True, "No active policy restrictions found."

        # Verify Cryptographic Signature
        expected_sig = self.db.calculate_policy_signature(
            policy["max_transaction_limit"],
            policy["daily_spending_limit"],
            policy["monthly_budget"],
            policy["emergency_stop"]
        )
        if policy.get("signature") != expected_sig:
            self.db.add_audit_log("POLICY_TAMPERED", "ALERT: Policy signature verification failed! Tampering detected.")
            # Automatically trigger Emergency Stop to protect the wallet
            self.db.update_policy(
                policy["max_transaction_limit"],
                policy["daily_spending_limit"],
                policy["monthly_budget"],
                1 # Enable Emergency Stop
            )
            return False, "Security Violation: Spending policies have been tampered with. Transactions frozen."

        # 1. Emergency Stop check
        if policy.get("emergency_stop", 0) == 1:
            self.db.add_audit_log("POLICY_BLOCKED", f"Blocked payment of ${amount} to {merchant}: Emergency stop is active.")
            return False, "Emergency stop switch is active. All financial transactions are frozen."

        # 2. Max Transaction Limit check
        max_limit = policy.get("max_transaction_limit", 1000.0)
        if amount > max_limit:
            self.db.add_audit_log("POLICY_BLOCKED", f"Blocked payment of ${amount} to {merchant}: Exceeds max limit of ${max_limit}.")
            return False, f"Transaction amount of ${amount} exceeds the single transaction limit of ${max_limit}."

        # 3. Daily Spending Limit check
        daily_limit = policy.get("daily_spending_limit", 5000.0)
        today_spent = self.db.get_today_spent()
        if today_spent + amount > daily_limit:
            self.db.add_audit_log("POLICY_BLOCKED", f"Blocked payment of ${amount} to {merchant}: Exceeds daily limit (Spent: ${today_spent}, Limit: ${daily_limit}).")
            return False, f"Daily limit exceeded. You have spent ${today_spent} today, and this transaction of ${amount} exceeds the daily limit of ${daily_limit}."

        # 4. Merchant check
        approved_merchants = policy.get("approved_merchants", [])
        if approved_merchants and merchant not in approved_merchants:
            self.db.add_audit_log("POLICY_BLOCKED", f"Blocked payment of ${amount} to {merchant}: Vendor not on whitelist.")
            return False, f"Merchant '{merchant}' is not in the approved vendors whitelist."

        # 5. Category check
        approved_categories = policy.get("approved_categories", [])
        if approved_categories and category not in approved_categories:
            self.db.add_audit_log("POLICY_BLOCKED", f"Blocked payment of ${amount} to {merchant}: Category '{category}' not on whitelist.")
            return False, f"Category '{category}' is not in the approved business categories whitelist."

        self.db.add_audit_log("POLICY_PASSED", f"Authorized proposed payment of ${amount} to {merchant}.")
        return True, "Authorized"
