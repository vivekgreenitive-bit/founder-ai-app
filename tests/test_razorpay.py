import unittest
import os
from db.payment_db import PaymentDBManager
from agents.payment_agent import PaymentAgent
from providers.razorpay_provider import RazorpayPaymentProvider

class TestRazorpayIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_razorpay.db"
        self.db = PaymentDBManager(self.db_path)
        self.agent = PaymentAgent(self.db, provider_type="razorpay")

    def tearDown(self):
        if hasattr(self.db, 'conn') and self.db.conn:
            self.db.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_razorpay_provider_initialization(self):
        self.assertEqual(self.agent.provider.provider_name(), "razorpay")
        self.assertIsInstance(self.agent.provider, RazorpayPaymentProvider)

    def test_razorpay_subscription_creation(self):
        res = self.agent.provider.create_subscription("plan_founder_pro", "founder@example.com")
        self.assertTrue(res["subscription_id"].startswith("sub_"))
        self.assertEqual(res["status"], "created")

    def test_razorpay_payment_signature_verification(self):
        verified = self.agent.provider.verify_payment_signature("order_123", "pay_456", "sig_789")
        self.assertTrue(verified)

if __name__ == "__main__":
    unittest.main()
