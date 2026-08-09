import unittest
from PyQt6.QtWidgets import QApplication
import sys

# Ensure single QApplication instance for PyQt tests
app = QApplication.instance() or QApplication(sys.argv)

from app import FounderApp

class TestNavigationStateSync(unittest.TestCase):
    def setUp(self):
        self.founder_app = FounderApp()

    def test_default_screen_is_today(self):
        """Verify Today (index 0) is default screen on startup."""
        self.assertEqual(self.founder_app.stacked_widget.currentIndex(), 0)
        self.assertTrue(self.founder_app.nav_buttons["today"].isChecked())

    def test_switch_nav_synchronizes_state(self):
        """Verify switching tabs updates both stacked widget index and sidebar button check states."""
        self.founder_app.switch_nav("diagnose")
        self.assertEqual(self.founder_app.stacked_widget.currentIndex(), 1)
        self.assertTrue(self.founder_app.nav_buttons["diagnose"].isChecked())
        self.assertFalse(self.founder_app.nav_buttons["today"].isChecked())

        self.founder_app.switch_nav("outcomes")
        self.assertEqual(self.founder_app.stacked_widget.currentIndex(), 3)
        self.assertTrue(self.founder_app.nav_buttons["outcomes"].isChecked())
        self.assertFalse(self.founder_app.nav_buttons["diagnose"].isChecked())

    def test_analysis_start_auto_switches_to_diagnose(self):
        """Verify starting an analysis automatically switches nav selection from Today to Diagnose."""
        self.founder_app.switch_nav("today")
        self.assertEqual(self.founder_app.stacked_widget.currentIndex(), 0)
        
        self.founder_app.query_input.setPlainText("Test challenge")
        self.founder_app.run_analysis()
        
        # Must automatically switch to Diagnose screen (index 1)
        self.assertEqual(self.founder_app.stacked_widget.currentIndex(), 1)
        self.assertTrue(self.founder_app.nav_buttons["diagnose"].isChecked())
        self.assertFalse(self.founder_app.nav_buttons["today"].isChecked())

if __name__ == "__main__":
    unittest.main()
