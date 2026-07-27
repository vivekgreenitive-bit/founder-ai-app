import unittest
from unittest.mock import MagicMock
from agents.framework_agent import FrameworkSelectionAgent

class TestFrameworkSelection(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock()
        self.agent = FrameworkSelectionAgent(self.mock_llm)

    def test_manual_framework_override_preservation(self):
        user_selection = "Please apply the framework: MC BEERS (Quarterly Planning)"
        
        # When manual framework is provided, the LLM should not be called
        result = self.agent.run(assessment={}, user_selected_framework=user_selection)
        
        self.mock_llm.invoke.assert_not_called()
        self.assertEqual(result["framework_name"], "MC BEERS")
        self.assertEqual(result["confidence"], 1.0)
        self.assertIn("User manually selected", result["reasoning"])

    def test_auto_framework_selection(self):
        # Setup mock behavior for LLM select
        self.mock_llm.invoke.return_value = "OKS REC SME\nSystem architecture is required for scaling."
        
        assessment = {
            "stage": "Growth ($1M - $10M)",
            "business_model": "SaaS / Software",
            "primary_challenge": "Bottlenecks in scaling the system"
        }
        
        result = self.agent.run(assessment=assessment, user_selected_framework=None)
        
        self.mock_llm.invoke.assert_called_once()
        self.assertEqual(result["framework_name"], "OKS REC SME")
        self.assertEqual(result["confidence"], 0.8)
        self.assertEqual(result["reasoning"], "System architecture is required for scaling.")

    def test_fallback_framework_selection(self):
        self.mock_llm.invoke.side_effect = Exception("Model Timeout")
        
        result = self.agent.run(assessment={}, user_selected_framework=None)
        
        self.assertEqual(result["framework_name"], "ECG KISS")
        self.assertEqual(result["confidence"], 0.5)
        self.assertIn("Fallback due to error", result["reasoning"])

if __name__ == '__main__':
    unittest.main()
