import unittest
import os
from agents.verification_agent import DecisionVerificationAgent
from db.outcome_tracker import OutcomeTrackerDB

class TestClosedLoopArchitecture(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_outcome.db"
        self.tracker = OutcomeTrackerDB(self.db_path)
        self.verifier = DecisionVerificationAgent(llm=None)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_decision_verification_high_confidence(self):
        evidence = {"revenue": 50000, "churn": 0.05, "cac": 120}
        res = self.verifier.verify_decision("High Churn", "Apply PC PEERS", evidence)
        self.assertGreaterEqual(res["confidence_score"], 0.75)
        self.assertTrue(res["is_sufficient"])
        self.assertEqual(res["verification_status"], "VERIFIED_HIGH_CONFIDENCE")

    def test_decision_verification_missing_evidence(self):
        evidence = {}
        res = self.verifier.verify_decision("Low Conversion", "Apply RUN DCMS ER", evidence)
        self.assertLess(res["confidence_score"], 0.70)
        self.assertFalse(res["is_sufficient"])
        self.assertEqual(res["verification_status"], "VERIFIED_NEEDS_MORE_DATA")

    def test_outcome_tracking_lifecycle(self):
        dec = self.tracker.record_decision("dec_101", "RUN DCMS ER", "Low Activation", "Activation Rate %", 31.0, 40.0)
        self.assertEqual(dec["status"], "IN_PROGRESS")
        
        outcome = self.tracker.record_outcome("dec_101", actual_value=43.0, arr_impact=18400.0)
        self.assertEqual(outcome["status"], "SUCCESS")
        self.assertEqual(outcome["arr_impact"], 18400.0)

if __name__ == "__main__":
    unittest.main()
