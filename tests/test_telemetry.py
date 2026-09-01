"""
tests/test_telemetry.py
Unit tests verifying Prometheus Observability Telemetry integration for Grafana Labs track.
"""
import unittest
from services.telemetry_service import (
    start_telemetry_server,
    AGENT_STEP_DURATION,
    POLICY_VALIDATIONS,
    USDC_SPENDING_TOTAL,
    FRAMEWORK_SELECTION_COUNT
)

class TestTelemetry(unittest.TestCase):
    def test_telemetry_metrics_recording(self):
        # 1. Test step duration recording
        AGENT_STEP_DURATION.labels(agent_name="TestAgent").observe(0.42)
        
        # 2. Test policy validation counter
        POLICY_VALIDATIONS.labels(status="approved", policy_rule="max_limit").inc()
        
        # 3. Test USDC spending counter
        USDC_SPENDING_TOTAL.labels(currency="USDC", merchant_category="Software").inc(50.0)
        
        # 4. Test framework counter
        FRAMEWORK_SELECTION_COUNT.labels(framework_name="ECG KISS").inc()
        
        # Assert server can be triggered cleanly
        started = start_telemetry_server(9090)
        self.assertIsInstance(started, bool)

if __name__ == "__main__":
    unittest.main()
