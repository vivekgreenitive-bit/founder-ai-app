import uuid
from typing import Dict, Any, List
from db.payment_db import PaymentDBManager
from agents.policy_engine import PolicyEngine
from providers.circle_provider import CirclePaymentProvider

class PaymentAgent:
    def __init__(self, db_manager: PaymentDBManager):
        self.db = db_manager
        self.policy_engine = PolicyEngine(self.db)
        self.provider = CirclePaymentProvider()

    def execute_payment_workflow(self, amount: float, merchant: str, category: str, destination_address: str) -> Dict[str, Any]:
        """
        Coordinates full payment: checks policies -> calls Circle USDC transfer -> updates local wallet ledger.
        """
        # 1. Evaluate Policy
        allowed, reason = self.policy_engine.evaluate(amount, merchant, category)
        tx_id = f"tx_{uuid.uuid4().hex[:12]}"
        
        wallet = self.db.get_wallet("primary_usdc_wallet")
        current_balance = wallet["usdc_balance"] if wallet else 0.0
        
        if not allowed:
            # Check if blocked or pending approval
            status = "pending_approval" if "exceeds" in reason or "limit" in reason else "failed"
            self.db.add_transaction(tx_id, "primary_usdc_wallet", amount, merchant, category, None, status)
            self.db.add_audit_log("PAYMENT_BLOCKED", f"Tx {tx_id} to {merchant} failed policy: {reason}")
            return {
                "success": False,
                "status": status,
                "transaction_id": tx_id,
                "reason": reason,
                "amount": amount,
                "merchant": merchant,
                "category": category
            }

        # 2. Insufficient funds check
        if current_balance < amount:
            self.db.add_transaction(tx_id, "primary_usdc_wallet", amount, merchant, category, None, "failed")
            self.db.add_audit_log("PAYMENT_FAILED", f"Tx {tx_id} failed: Insufficient USDC balance.")
            return {
                "success": False,
                "status": "failed",
                "transaction_id": tx_id,
                "reason": "Insufficient wallet USDC funds.",
                "amount": amount,
                "merchant": merchant,
                "category": category
            }

        # 3. Execute transfer on Circle
        try:
            circle_tx_id = self.provider.execute_payment("primary_usdc_wallet", destination_address, amount)
            new_balance = current_balance - amount
            self.db.update_wallet_balance("primary_usdc_wallet", new_balance)
            
            self.db.add_transaction(tx_id, "primary_usdc_wallet", amount, merchant, category, circle_tx_id, "completed")
            self.db.add_audit_log("PAYMENT_SUCCESS", f"Successfully sent {amount} USDC to {merchant} via Circle Tx {circle_tx_id}.")
            
            return {
                "success": True,
                "status": "completed",
                "transaction_id": tx_id,
                "circle_tx_id": circle_tx_id,
                "amount": amount,
                "merchant": merchant,
                "category": category,
                "remaining_balance": new_balance
            }
        except Exception as e:
            self.db.add_transaction(tx_id, "primary_usdc_wallet", amount, merchant, category, None, "failed")
            self.db.add_audit_log("PAYMENT_FAILED", f"Tx {tx_id} failed Circle execution: {str(e)}")
            return {
                "success": False,
                "status": "failed",
                "transaction_id": tx_id,
                "reason": f"Circle provider execution failed: {str(e)}",
                "amount": amount,
                "merchant": merchant,
                "category": category
            }

    def process_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Receives a customer payment against an unpaid invoice."""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, customer_name, amount, status FROM invoices WHERE id = ?", (invoice_id,))
        row = cursor.fetchone()
        
        if not row:
            return {"success": False, "reason": "Invoice not found."}
            
        customer, amount, status = row[1], row[2], row[3]
        if status == "paid":
            return {"success": False, "reason": "Invoice is already paid."}

        # Simulate receiving USDC
        wallet = self.db.get_wallet("primary_usdc_wallet")
        current_balance = wallet["usdc_balance"] if wallet else 0.0
        new_balance = current_balance + amount
        
        self.db.update_wallet_balance("primary_usdc_wallet", new_balance)
        cursor.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (invoice_id,))
        self.db.conn.commit()
        
        tx_id = f"tx_recv_{uuid.uuid4().hex[:8]}"
        self.db.add_transaction(tx_id, "primary_usdc_wallet", amount, customer, "Inbound Sales", f"circle_recv_{invoice_id}", "completed")
        self.db.add_audit_log("INVOICE_PAID", f"Received customer payment of {amount} USDC from {customer} for invoice {invoice_id}.")
        
        return {
            "success": True,
            "invoice_id": invoice_id,
            "amount": amount,
            "customer": customer,
            "new_balance": new_balance
        }

    def renew_subscriptions(self) -> List[Dict[str, Any]]:
        """Scans active subscriptions and automatically renews due items."""
        subs = self.db.get_all_subscriptions()
        renewals = []
        
        for sub in subs:
            if sub["status"] == "active":
                # Execute payment logic (standard category Subscription)
                res = self.execute_payment_workflow(
                    amount=sub["cost"],
                    merchant=sub["service"],
                    category="Subscriptions",
                    destination_address="0xsubscription_address_placeholder"
                )
                renewals.append({"service": sub["service"], "result": res})
                
        return renewals

    def reconcile_wallets(self) -> Dict[str, Any]:
        """Syncs circle sandbox balance with database balance."""
        wallet = self.db.get_wallet("primary_usdc_wallet")
        if not wallet:
            return {"success": False, "reason": "No wallet found."}
            
        circle_balance = self.provider.get_wallet_balance(wallet["id"])
        self.db.update_wallet_balance(wallet["id"], circle_balance)
        self.db.add_audit_log("RECONCILIATION", f"Reconciled wallet balance to match Circle Testnet balance of {circle_balance} USDC.")
        return {"success": True, "reconciled_balance": circle_balance}
