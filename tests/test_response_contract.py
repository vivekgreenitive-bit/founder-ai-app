import unittest
from unittest.mock import MagicMock
from agents.orchestrator import OrchestratorAgent

class TestResponseContract(unittest.TestCase):
    def setUp(self):
        self.orchestrator = OrchestratorAgent(MagicMock(), MagicMock())

    def test_valid_response_format(self):
        valid_response = (
            "## 1. Framework Selected\n"
            "ECG KISS\n"
            "This framework fits because we need to define the end goal.\n\n"
            "## 2. Executive Summary\n"
            "This is a high level business summary of 120 words directly answering the question.\n\n"
            "## 3. Framework Analysis\n"
            "Detailed analysis of variables.\n\n"
            "## 4. Recommendation\n"
            "Key strategic recommendations and alternatives.\n\n"
            "## 5. Priority Actions\n"
            "Implement tracking immediately.\n\n"
            "## 6. Next 24 Hours\n"
            "Schedule a call to document processes.\n\n"
            "## 7. Risks and Missing Information\n"
            "Keep the monitoring scope focused.\n\n"
            "## 8. Suggested Follow-up Questions\n"
            "1. Question one?\n"
            "2. Question two?"
        )
        is_valid, reason = self.orchestrator.validate_response(valid_response)
        self.assertTrue(is_valid, f"Expected valid, got: {reason}")

    def test_missing_header(self):
        invalid_response = (
            "## 1. Framework Selected\n"
            "ECG KISS\n\n"
            "## 2. Executive Summary\n"
            "This is a high level business summary.\n\n"
            # Missing 3. Framework Analysis
            "## 4. Recommendation\n"
            "Key strategic recommendations.\n\n"
            "## 5. Priority Actions\n"
            "Implement tracking immediately.\n\n"
            "## 6. Next 24 Hours\n"
            "Schedule a call.\n\n"
            "## 7. Risks and Missing Information\n"
            "Keep the monitoring scope focused.\n\n"
            "## 8. Suggested Follow-up Questions\n"
            "1. Question one?"
        )
        is_valid, reason = self.orchestrator.validate_response(invalid_response)
        self.assertFalse(is_valid)
        self.assertIn("Missing header pattern", reason)

    def test_invalid_framework_name(self):
        invalid_response = (
            "## 1. Framework Selected\n"
            "MY MADE UP FRAMEWORK\n\n"
            "## 2. Executive Summary\n"
            "This is a high level business summary.\n\n"
            "## 3. Framework Analysis\n"
            "Detailed analysis of variables.\n\n"
            "## 4. Recommendation\n"
            "Key strategic recommendations.\n\n"
            "## 5. Priority Actions\n"
            "Implement tracking immediately.\n\n"
            "## 6. Next 24 Hours\n"
            "Schedule a call.\n\n"
            "## 7. Risks and Missing Information\n"
            "Keep the monitoring scope focused.\n\n"
            "## 8. Suggested Follow-up Questions\n"
            "1. Question one?"
        )
        is_valid, reason = self.orchestrator.validate_response(invalid_response)
        self.assertFalse(is_valid)
        self.assertIn("Invalid framework name", reason)

    def test_empty_section(self):
        invalid_response = (
            "## 1. Framework Selected\n"
            "ECG KISS\n\n"
            "## 2. Executive Summary\n"
            "\n\n"  # Empty section
            "## 3. Framework Analysis\n"
            "Detailed analysis of variables.\n\n"
            "## 4. Recommendation\n"
            "Key strategic recommendations.\n\n"
            "## 5. Priority Actions\n"
            "Implement tracking immediately.\n\n"
            "## 6. Next 24 Hours\n"
            "Schedule a call.\n\n"
            "## 7. Risks and Missing Information\n"
            "Keep the monitoring scope focused.\n\n"
            "## 8. Suggested Follow-up Questions\n"
            "1. Question one?"
        )
        is_valid, reason = self.orchestrator.validate_response(invalid_response)
        self.assertFalse(is_valid)
        self.assertIn("empty", reason)

    def test_instruction_leak(self):
        invalid_response = (
            "## 1. Framework Selected\n"
            "ECG KISS\n\n"
            "## 2. Executive Summary\n"
            "Summary.\n\n"
            "## 3. Framework Analysis\n"
            "Detailed analysis of variables.\n\n"
            "## 4. Recommendation\n"
            "---DREAMER---\n"  # Leaked instruction label
            "Key strategic recommendations.\n\n"
            "## 5. Priority Actions\n"
            "Implement tracking immediately.\n\n"
            "## 6. Next 24 Hours\n"
            "Schedule a call.\n\n"
            "## 7. Risks and Missing Information\n"
            "Keep the monitoring scope focused.\n\n"
            "## 8. Suggested Follow-up Questions\n"
            "1. Question one?"
        )
        is_valid, reason = self.orchestrator.validate_response(invalid_response)
        self.assertFalse(is_valid)
        self.assertIn("Internal label/leak detected", reason)

    def test_cloud_api_leak(self):
        invalid_response = (
            "## 1. Framework Selected\n"
            "ECG KISS\n\n"
            "## 2. Executive Summary\n"
            "Summary.\n\n"
            "## 3. Framework Analysis\n"
            "We integrated OpenAI APIs into the product.\n\n"
            "## 4. Recommendation\n"
            "Key strategic recommendations.\n\n"
            "## 5. Priority Actions\n"
            "Implement tracking immediately.\n\n"
            "## 6. Next 24 Hours\n"
            "Schedule a call.\n\n"
            "## 7. Risks and Missing Information\n"
            "Keep the monitoring scope focused.\n\n"
            "## 8. Suggested Follow-up Questions\n"
            "1. Question one?"
        )
        is_valid, reason = self.orchestrator.validate_response(invalid_response)
        self.assertFalse(is_valid)
        self.assertIn("Cloud API reference detected", reason)

if __name__ == '__main__':
    unittest.main()
