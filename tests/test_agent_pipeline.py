import unittest
from unittest.mock import MagicMock, patch
from agents.orchestrator import OrchestratorAgent

class TestAgentPipeline(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock()
        self.mock_vectorstore = MagicMock()
        self.orchestrator = OrchestratorAgent(self.mock_llm, self.mock_vectorstore)

    @patch('agents.orchestrator.AssessmentAgent')
    @patch('agents.orchestrator.FrameworkSelectionAgent')
    @patch('agents.orchestrator.KnowledgeRetrievalAgent')
    @patch('agents.orchestrator.MemoryAgent')
    @patch('agents.orchestrator.StrategyAgent')
    @patch('agents.orchestrator.ExecutionCoachAgent')
    @patch('agents.orchestrator.ResponseComposer')
    def test_genuine_agent_invocation_sequence(self, MockResponseComposer, MockExecutionCoachAgent, 
                                               MockStrategyAgent, MockMemoryAgent, MockKnowledgeRetrievalAgent, 
                                               MockFrameworkSelectionAgent, MockAssessmentAgent):
        # Setup mocks
        mock_assessment_instance = MockAssessmentAgent.return_value
        mock_assessment_instance.run.return_value = {
            "stage": "Pre-revenue", "business_model": "SaaS", "maturity": "Low", 
            "primary_challenge": "No clients", "missing_info": [], "summary": "Idea stage"
        }
        
        mock_framework_instance = MockFrameworkSelectionAgent.return_value
        mock_framework_instance.run.return_value = {
            "framework_name": "ECG KISS", "confidence": 1.0, "reasoning": "Standard"
        }
        
        mock_retrieval_instance = MockKnowledgeRetrievalAgent.return_value
        mock_retrieval_instance.run.return_value = "Retrieved proprietary context."
        
        mock_memory_instance = MockMemoryAgent.return_value
        mock_memory_instance.get_context.return_value = "Memory context."
        
        mock_strategy_instance = MockStrategyAgent.return_value
        mock_strategy_instance.run.return_value = {
            "scenario": "Some scenario details",
            "applied_sections": "Some applied sections details",
            "dreamer": "Some dreamer details",
            "guardian": "Some guardian details"
        }
        
        mock_execution_instance = MockExecutionCoachAgent.return_value
        mock_execution_instance.run.return_value = {
            "priority_action": "Do this first",
            "athlete": "1. Step A\n2. Step B\n3. Step C"
        }
        
        mock_composer_instance = MockResponseComposer.return_value
        mock_composer_instance.run.return_value = (
            "## 1. Business Scenario\nSome scenario details\n\n"
            "## 2. Framework Name\nECG KISS\n\n"
            "## 3. Applied Sections\nSome applied sections details\n\n"
            "## 4. Priority Action\nDo this first\n\n"
            "## 5. Dreamer\nSome dreamer details\n\n"
            "## 6. Guardian\nSome guardian details\n\n"
            "## 7. Athlete\n1. Step A\n2. Step B\n3. Step C"
        )
        
        # Instantiate orchestrator with mocks loaded
        orchestrator = OrchestratorAgent(self.mock_llm, self.mock_vectorstore)
        
        # Override fields with mocked instances
        orchestrator.assessment_agent = mock_assessment_instance
        orchestrator.framework_agent = mock_framework_instance
        orchestrator.retrieval_agent = mock_retrieval_instance
        orchestrator.memory_agent = mock_memory_instance
        orchestrator.strategy_agent = mock_strategy_instance
        orchestrator.execution_agent = mock_execution_instance
        orchestrator.response_composer = mock_composer_instance
        
        query = "How to validate BakerConnect?"
        doc_text = "Baker details."
        profile = {"stage": "Pre-revenue"}
        
        # Call the orchestrator
        status_updates = []
        def status_callback(msg):
            status_updates.append(msg)
            
        result = orchestrator.run(query, doc_text, profile, status_callback=status_callback)
        
        # Verify genuine executions
        mock_assessment_instance.run.assert_called_once_with(query, doc_text, profile)
        mock_framework_instance.run.assert_called_once_with(mock_assessment_instance.run.return_value, None)
        mock_retrieval_instance.run.assert_called_once_with(query, "ECG KISS")
        mock_memory_instance.get_context.assert_called_once()
        mock_strategy_instance.run.assert_called_once()
        mock_execution_instance.run.assert_called_once()
        mock_composer_instance.run.assert_called_once()
        mock_memory_instance.add_record.assert_called_once_with(query, "ECG KISS", result)
        
        # Check status callback sequence
        self.assertIn("Understanding your business challenge", status_updates)
        self.assertIn("Selecting the relevant Founder Framework", status_updates)
        self.assertIn("Retrieving framework knowledge", status_updates)
        self.assertIn("Developing the strategy", status_updates)
        self.assertIn("Building the execution plan", status_updates)
        self.assertIn("Finalizing the recommendation", status_updates)
        
        # Verify validator passed
        self.assertTrue(result.startswith("## 1. Business Scenario"))

if __name__ == '__main__':
    unittest.main()
