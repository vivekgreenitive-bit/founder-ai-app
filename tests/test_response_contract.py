import unittest
from unittest.mock import MagicMock
from agents.orchestrator import OrchestratorAgent

class TestResponseContract(unittest.TestCase):
    def setUp(self):
        self.orchestrator = OrchestratorAgent(MagicMock(), MagicMock())

    def test_valid_response_format(self):
        valid_response = (
            "## 1. Business Scenario\n"
            "This is a description of the startup scenario.\n\n"
            "## 2. Framework Name\n"
            "ECG KISS\n\n"
            "## 3. Applied Sections\n"
            "Applying E, C, and G variables with details.\n\n"
            "## 4. Priority Action\n"
            "Implement primary metric tracking.\n\n"
            "## 5. Dreamer\n"
            "Expansion options and high growth details.\n\n"
            "## 6. Guardian\n"
            "Risk profiles and operations monitoring.\n\n"
            "## 7. Athlete\n"
            "1. Task one\n"
            "2. Task two\n"
            "3. Task three"
        )
        is_valid, reason = self.orchestrator.validate_response(valid_response)
        self.assertTrue(is_valid, f"Expected valid, got: {reason}")

    def test_missing_header(self):
        invalid_response = (
            "## 1. Business Scenario\n"
            "Scenario info.\n\n"
            "## 2. Framework Name\n"
            "ECG KISS\n\n"
            # Missing Applied Sections
            "## 4. Priority Action\n"
            "Action item.\n\n"
            "## 5. Dreamer\n"
            "Dreamer info.\n\n"
            "## 6. Guardian\n"
            "Guardian info.\n\n"
            "## 7. Athlete\n"
            "Athlete info."
        )
        is_valid, reason = self.orchestrator.validate_response(invalid_response)
        self.assertFalse(is_valid)
        self.assertIn("Missing header pattern", reason)

    def test_invalid_framework_name(self):
        invalid_response = (
            "## 1. Business Scenario\n"
            "Scenario info.\n\n"
            "## 2. Framework Name\n"
            "MY MADE UP FRAMEWORK\n\n"
            "## 3. Applied Sections\n"
            "Applied sections info.\n\n"
            "## 4. Priority Action\n"
            "Action item.\n\n"
            "## 5. Dreamer\n"
            "Dreamer info.\n\n"
            "## 6. Guardian\n"
            "Guardian info.\n\n"
            "## 7. Athlete\n"
            "Athlete info."
        )
        is_valid, reason = self.orchestrator.validate_response(invalid_response)
        self.assertFalse(is_valid)
        self.assertIn("Invalid framework name", reason)

    def test_empty_section(self):
        invalid_response = (
            "## 1. Business Scenario\n"
            "Scenario info.\n\n"
            "## 2. Framework Name\n"
            "ECG KISS\n\n"
            "## 3. Applied Sections\n"
            "\n\n"  # Empty section
            "## 4. Priority Action\n"
            "Action item.\n\n"
            "## 5. Dreamer\n"
            "Dreamer info.\n\n"
            "## 6. Guardian\n"
            "Guardian info.\n\n"
            "## 7. Athlete\n"
            "Athlete info."
        )
        is_valid, reason = self.orchestrator.validate_response(invalid_response)
        self.assertFalse(is_valid)
        self.assertIn("empty", reason)

    def test_instruction_leak(self):
        invalid_response = (
            "## 1. Business Scenario\n"
            "Scenario info.\n\n"
            "## 2. Framework Name\n"
            "ECG KISS\n\n"
            "## 3. Applied Sections\n"
            "Applied info.\n\n"
            "## 4. Priority Action\n"
            "Action info.\n\n"
            "## 5. Dreamer\n"
            "Dreamer info.\n\n"
            "## 6. Guardian\n"
            "---DREAMER---\n"  # Leaked instruction label
            "Guardian info.\n\n"
            "## 7. Athlete\n"
            "Athlete info."
        )
        is_valid, reason = self.orchestrator.validate_response(invalid_response)
        self.assertFalse(is_valid)
        self.assertIn("Internal label/leak detected", reason)

    def test_cloud_api_leak(self):
        invalid_response = (
            "## 1. Business Scenario\n"
            "Scenario info.\n\n"
            "## 2. Framework Name\n"
            "ECG KISS\n\n"
            "## 3. Applied Sections\n"
            "We integrated OpenAI APIs into the product.\n\n"
            "## 4. Priority Action\n"
            "Action info.\n\n"
            "## 5. Dreamer\n"
            "Dreamer info.\n\n"
            "## 6. Guardian\n"
            "Guardian info.\n\n"
            "## 7. Athlete\n"
            "Athlete info."
        )
        is_valid, reason = self.orchestrator.validate_response(invalid_response)
        self.assertFalse(is_valid)
        self.assertIn("Cloud API reference detected", reason)

if __name__ == '__main__':
    unittest.main()
