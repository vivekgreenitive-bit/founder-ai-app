"""
services/telemetry_service.py
Prometheus Observability Telemetry Service for Founder AI Multi-Agent Engine.
Exposes real-time metrics for Grafana Cloud & Local Grafana Dashboards.
"""
import time
import logging
from typing import Optional
from prometheus_client import start_http_server, Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# ── Prometheus Metrics Definitions ──────────────────────────────────────────

# Multi-Agent Stage Execution Latency
AGENT_STEP_DURATION = Histogram(
    "founder_ai_agent_step_duration_seconds",
    "Time spent in seconds in each agent stage of the reasoning pipeline",
    ["agent_name"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)

# Overall Pipeline Execution Duration
PIPELINE_TOTAL_DURATION = Histogram(
    "founder_ai_pipeline_total_duration_seconds",
    "Total execution time in seconds for complete multi-agent diagnosis pipeline",
    buckets=(0.5, 1.0, 3.0, 5.0, 10.0, 20.0, 45.0, 90.0)
)

# Policy Engine Governance Counter
POLICY_VALIDATIONS = Counter(
    "founder_ai_policy_validations_total",
    "Total number of governance policy verification checks executed",
    ["status", "policy_rule"]
)

# Payment Transactions Counter
USDC_SPENDING_TOTAL = Counter(
    "founder_ai_usdc_spending_total",
    "Total volume of USDC payments processed by PaymentAgent",
    ["currency", "merchant_category"]
)

# Framework Selection Counter
FRAMEWORK_SELECTION_COUNT = Counter(
    "founder_ai_framework_selection_total",
    "Frequency of Founder Frameworks auto-selected by FrameworkSelectionAgent",
    ["framework_name"]
)

# Gemini / Provider Token Usage
LLM_TOKEN_COUNT = Counter(
    "founder_ai_llm_tokens_total",
    "Estimated total LLM tokens consumed across multi-agent calls",
    ["provider", "agent_name"]
)

# Active System Gauges
ACTIVE_PIPELINE_GAUGE = Gauge(
    "founder_ai_active_pipelines",
    "Number of currently running multi-agent diagnosis pipelines"
)

# ── Server Manager ───────────────────────────────────────────────────────────

_SERVER_STARTED = False

def start_telemetry_server(port: int = 9090) -> bool:
    """
    Starts the Prometheus HTTP metrics exporter server on the specified port.
    Returns True if started successfully, False if already running.
    """
    global _SERVER_STARTED
    if _SERVER_STARTED:
        logger.debug("Telemetry server already running.")
        return False
    
    try:
        start_http_server(port)
        _SERVER_STARTED = True
        logger.info(f"🚀 Prometheus Observability Telemetry Exporter running at http://localhost:{port}/metrics")
        return True
    except Exception as e:
        logger.error(f"Failed to start Prometheus telemetry server on port {port}: {e}")
        return False
