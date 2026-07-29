import unittest
import os
import shutil
from unittest.mock import MagicMock
from db.payment_db import PaymentDBManager
from agents.policy_engine import PolicyEngine
from agents.payment_agent import PaymentAgent
from agents.orchestrator import OrchestratorAgent

class TestPaymentSystem(unittest.TestCase):
    def setUp(self):
        # Use a temporary test SQLite database to avoid mutating production data
        self.test_db_path = "test_conversation_history.db"
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
            
        self.db = PaymentDBManager(self.test_db_path)
        self.policy_engine = PolicyEngine(self.db)
        self.payment_agent = PaymentAgent(self.db)

    def tearDown(self):
        # Clean up database connection and delete test file
        self.db.conn.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_database_init_seeding(self):
        # Assert default seeded wallet and policy exist
        wallet = self.db.get_wallet("primary_usdc_wallet")
        self.assertIsNotNone(wallet)
        self.assertEqual(wallet["usdc_balance"], 1500.00)

        policy = self.db.get_active_policy()
        self.assertIsNotNone(policy)
        self.assertEqual(policy["max_transaction_limit"], 200.0)

    def test_policy_engine_emergency_stop(self):
        # Activate emergency stop
        self.db.update_policy(200.0, 500.0, 2000.0, 1)
        allowed, reason = self.policy_engine.evaluate(50.0, "Gartner", "Research")
        self.assertFalse(allowed)
        self.assertIn("Emergency stop", reason)

    def test_policy_engine_max_transaction_limit(self):
        # Under limit
        allowed, reason = self.policy_engine.evaluate(50.0, "Gartner", "Research")
        self.assertTrue(allowed)

        # Over limit ($250 proposed spend vs $200 max policy limit)
        allowed, reason = self.policy_engine.evaluate(250.0, "Gartner", "Research")
        self.assertFalse(allowed)
        self.assertIn("exceeds the single transaction limit", reason)

    def test_policy_engine_daily_spending_limit(self):
        # Seed a completed transaction that consumes most of the daily budget
        self.db.add_transaction("tx_dummy_1", "primary_usdc_wallet", 450.0, "Gartner", "Research", "circle_tx_1", "completed")
        
        # Proposed spend of $100 + $450 = $550, exceeding the $500 daily spending limit
        allowed, reason = self.policy_engine.evaluate(100.0, "Gartner", "Research")
        self.assertFalse(allowed)
        self.assertIn("Daily limit exceeded", reason)

    def test_payment_agent_insufficient_funds(self):
        # Set wallet balance to $10
        self.db.update_wallet_balance("primary_usdc_wallet", 10.00)
        
        # Proposed spend of $50 (policy allows up to $200)
        res = self.payment_agent.execute_payment_workflow(50.0, "Gartner", "Research", "0xaddr")
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "failed")
        self.assertIn("Insufficient wallet USDC", res["reason"])

    def test_payment_agent_successful_transaction(self):
        # Execute workflow
        res = self.payment_agent.execute_payment_workflow(50.0, "Gartner", "Research", "0xaddr")
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["remaining_balance"], 1450.00)

        # Check transaction logged in database
        txs = self.db.get_all_transactions()
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0]["amount"], 50.0)
        self.assertEqual(txs[0]["merchant"], "Gartner")

    def test_payment_agent_invoice_processing(self):
        # Process unpaid invoice inv_001
        res = self.payment_agent.process_invoice("inv_001")
        self.assertTrue(res["success"])
        self.assertEqual(res["new_balance"], 2000.00) # $1500 starting + $500 invoice payment

        # Check invoice status updated to paid
        invoices = self.db.get_all_invoices()
        self.assertEqual(invoices[0]["status"], "paid")

    def test_orchestrator_payment_interception(self):
        mock_llm = MagicMock()
        # Mock LLM to return a payment intent JSON structure
        mock_llm.invoke.return_value = '{"amount": 49.00, "merchant": "Zoom", "category": "Subscriptions", "action": "pay", "destination": "0xaddr"}'
        
        orchestrator = OrchestratorAgent(mock_llm, MagicMock())
        orchestrator.payment_db = self.db
        orchestrator.payment_agent = self.payment_agent

        # Call orchestrator with payment query
        res = orchestrator.run("Please renew my Zoom subscription for $49", "", {})
        self.assertIn("PAYMENT RECEIPT", res)
        self.assertIn("49.0 USDC", res)
        self.assertIn("ZOOM", res.upper())

if __name__ == '__main__':
    unittest.main()
