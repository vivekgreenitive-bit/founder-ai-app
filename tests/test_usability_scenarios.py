import unittest
from unittest.mock import MagicMock
from agents.response_composer import ResponseComposer
from agents.orchestrator import OrchestratorAgent

class TestUsabilityScenarios(unittest.TestCase):
    def setUp(self):
        self.composer = ResponseComposer()
        self.orchestrator = OrchestratorAgent(MagicMock(), MagicMock())

    def test_scenario_1_saas_validation(self):
        """Scenario 1: Pre-revenue SaaS struggling to find early clients."""
        strategy = {
            "scenario": "A B2B SaaS startup needs to validate client demand before building full features.",
            "applied_sections": "E - End Goal: Validate 10 paying customers.\nC - Pain Points: Zero client traffic.\nG - Gap: Product exists but no user data.",
            "dreamer": "Launch a simple landing page with an interactive prototype.",
            "guardian": "Avoid building backend code before securing pre-signups."
        }
        execution = {
            "recommendation": "We recommend launching a landing page first before writing backend code.",
            "priority_action": "Build and launch a landing page with a waitlist form.",
            "athlete": "Share landing page with 50 targeted B2B prospects."
        }
        
        result = self.composer.run("ECG KISS", strategy, execution)
        is_valid, reason = self.orchestrator.validate_response(result)
        self.assertTrue(is_valid, f"Scenario 1 failed validation: {reason}")

    def test_scenario_2_ecommerce_pmf(self):
        """Scenario 2: E-commerce fashion brand struggling to scale sales."""
        strategy = {
            "scenario": "Direct-to-consumer apparel brand faces high customer acquisition cost (CAC).",
            "applied_sections": "S - Select Niche: Premium workout wear.\nL - Launch Fast: Target Instagram ads.\nR - Repeat Sales: Set up email retention.",
            "dreamer": "Create high-converting user generated content ads.",
            "guardian": "Ensure inventory is not over-purchased before scaling ad spend."
        }
        execution = {
            "recommendation": "Focus marketing on existing workout wear audience instead of general sports wear.",
            "priority_action": "Design and launch one email flow for abandoned carts.",
            "athlete": "Draft copy for 3 cart recovery emails."
        }
        
        result = self.composer.run("SLR CAMERAS", strategy, execution)
        is_valid, reason = self.orchestrator.validate_response(result)
        self.assertTrue(is_valid, f"Scenario 2 failed validation: {reason}")

    def test_scenario_3_agency_burnout(self):
        """Scenario 3: Services agency facing employee burnout due to custom work."""
        strategy = {
            "scenario": "Marketing agency is operating at max capacity but revenue has plateaued.",
            "applied_sections": "P - Productize: Sell fixed-price packages.\nC - Core Offer: Focus only on SEO audit.\nP - Pipeline: Automate booking.",
            "dreamer": "Standardize custom SEO packages into a productized subscription service.",
            "guardian": "Set clear boundaries on client revisions to prevent scope creep."
        }
        execution = {
            "recommendation": "Offer standard fixed-price SEO packages rather than custom scopes.",
            "priority_action": "Draft a single-page scope of work for the productized offer.",
            "athlete": "List key inclusions and exclusions on a single page."
        }
        
        result = self.composer.run("PC PEERS", strategy, execution)
        is_valid, reason = self.orchestrator.validate_response(result)
        self.assertTrue(is_valid, f"Scenario 3 failed validation: {reason}")

    def test_scenario_4_iot_fundraising(self):
        """Scenario 4: Hardware IoT startup pitching seed investors."""
        strategy = {
            "scenario": "IoT ag-tech startup needs to raise $500k to manufacture the first hardware batch.",
            "applied_sections": "M - Market Size: 10,000 local commercial farms.\nC - Competitive Advantage: Proprietary low-power sensor mesh.",
            "dreamer": "Focus pitch on massive agricultural utility savings.",
            "guardian": "Keep hardware manufacturing lead times under 90 days."
        }
        execution = {
            "recommendation": "Secure pre-orders from local farms before initiating pitch decks.",
            "priority_action": "Draft a 10-slide pitch deck highlighting unit economics.",
            "athlete": "Calculate detailed manufacturing costs for 100 units."
        }
        
        result = self.composer.run("MC BEERS", strategy, execution)
        is_valid, reason = self.orchestrator.validate_response(result)
        self.assertTrue(is_valid, f"Scenario 4 failed validation: {reason}")

    def test_scenario_5_consultancy_sops(self):
        """Scenario 5: Business consultancy aiming to delegate delivery tasks."""
        strategy = {
            "scenario": "Boutique consultancy needs to delegate audit reports to junior associates.",
            "applied_sections": "R - Record: Screen record audit process.\nS - Step-by-Step: Write checklists.\nS - Scale: Assign to associate.",
            "dreamer": "Build an internal knowledge base of reusable checklist templates.",
            "guardian": "Manually QA the first 5 associate reports before client delivery."
        }
        execution = {
            "recommendation": "Delegate task auditing via recorded screen tutorials.",
            "priority_action": "Create a Loom recording of a standard client audit process.",
            "athlete": "Record screen performing a mock client audit."
        }
        
        result = self.composer.run("RSS FEED SME", strategy, execution)
        is_valid, reason = self.orchestrator.validate_response(result)
        self.assertTrue(is_valid, f"Scenario 5 failed validation: {reason}")

if __name__ == '__main__':
    unittest.main()
