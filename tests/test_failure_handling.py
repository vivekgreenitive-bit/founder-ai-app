import unittest
from unittest.mock import MagicMock, patch
import os
import json
from document_processor import extract_text_from_file

class TestFailureHandling(unittest.TestCase):

    @patch('ai_engine.FounderAIEngine.init_llm')
    @patch('ai_engine.FounderAIEngine.init_vectorstore')
    @patch('ai_engine.HuggingFaceEmbeddings')
    def test_missing_company_profile(self, mock_embed, mock_init_vs, mock_init_llm):
        from ai_engine import FounderAIEngine
        profile_path = "company_profile.json"
        backup_path = "company_profile.json.bak"
        profile_existed = os.path.exists(profile_path)
        
        if profile_existed:
            os.rename(profile_path, backup_path)
            
        try:
            engine = FounderAIEngine()
            engine.orchestrator = MagicMock()
            engine.orchestrator.run.return_value = "Response"
            res = engine.analyze_query("Help me scale my business")
            self.assertIsNotNone(res)
        finally:
            if profile_existed:
                os.rename(backup_path, profile_path)

    @patch('ai_engine.FounderAIEngine.init_llm')
    @patch('ai_engine.FounderAIEngine.init_vectorstore')
    @patch('ai_engine.HuggingFaceEmbeddings')
    def test_invalid_company_profile(self, mock_embed, mock_init_vs, mock_init_llm):
        from ai_engine import FounderAIEngine
        profile_path = "company_profile.json"
        backup_path = "company_profile.json.bak"
        profile_existed = os.path.exists(profile_path)
        
        if profile_existed:
            os.rename(profile_path, backup_path)
            
        # Write corrupted profile
        with open(profile_path, "w") as f:
            f.write("{invalid_json_data:")
            
        try:
            engine = FounderAIEngine()
            engine.orchestrator = MagicMock()
            engine.orchestrator.run.return_value = "Response"
            res = engine.analyze_query("Help me scale my business")
            self.assertIsNotNone(res)
        finally:
            os.remove(profile_path)
            if profile_existed:
                os.rename(backup_path, profile_path)

    @patch('app.FounderAIEngine')
    def test_empty_user_request(self, mock_engine_class):
        # Testing local behavior of PyQt main app handler for empty query
        from app import FounderApp
        from PyQt6.QtWidgets import QApplication
        import sys
        
        # Initialize QApplication if not already done
        app_instance = QApplication.instance()
        if not app_instance:
            app_instance = QApplication(sys.argv)
            
        with patch('app.QMessageBox.warning') as mock_warn:
            app = FounderApp()
            app.query_input.setPlainText("")
            app.current_document_text = ""
            app.run_analysis()
            mock_warn.assert_called_once()

    def test_unsupported_file_parsing(self):
        res = extract_text_from_file("nonexistent_file.xyz")
        self.assertTrue(res.startswith("Error") or "not found" in res.lower() or "unsupported" in res.lower())

if __name__ == '__main__':
    unittest.main()
