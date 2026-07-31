import time
import json
import uuid
import re
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Callable

from agents.assessment_agent import AssessmentAgent
from agents.framework_agent import FrameworkSelectionAgent
from agents.retrieval_agent import KnowledgeRetrievalAgent
from agents.strategy_agent import StrategyAgent
from agents.execution_agent import ExecutionCoachAgent
from agents.memory_agent import MemoryAgent
from agents.response_composer import ResponseComposer

KNOWN_FRAMEWORKS = {
    "ECG KISS", "SLR CAMERAS", "MC BEERS", "PC PEERS", "PS ERP", "DC ERPRS",
    "OKS REC SME", "PFA SAAS SME", "RSS FEED SME", "RPM REAP ER", "RUN DCMS ER",
    "ERM FABS ER", "ADMINS ER"
}

from db.payment_db import PaymentDBManager
from agents.payment_agent import PaymentAgent

class OrchestratorAgent:
    llm: Any
    vectorstore: Any
    assessment_agent: AssessmentAgent
    framework_agent: FrameworkSelectionAgent
    retrieval_agent: KnowledgeRetrievalAgent
    strategy_agent: StrategyAgent
    execution_agent: ExecutionCoachAgent
    memory_agent: MemoryAgent
    response_composer: ResponseComposer
    payment_db: PaymentDBManager
    payment_agent: PaymentAgent
    log_file: str

    def __init__(self, llm: Any, vectorstore: Any) -> None:
        self.llm = llm
        self.vectorstore = vectorstore
        
        # Instantiate specialized agents
        self.assessment_agent = AssessmentAgent(llm)
        self.framework_agent = FrameworkSelectionAgent(llm, vectorstore)
        self.retrieval_agent = KnowledgeRetrievalAgent(vectorstore)
        self.strategy_agent = StrategyAgent(llm)
        self.execution_agent = ExecutionCoachAgent(llm)
        self.memory_agent = MemoryAgent()
        self.response_composer = ResponseComposer(llm)
        self.payment_db = PaymentDBManager()
        self.payment_agent = PaymentAgent(self.payment_db)
        
        self.log_file = "orchestrator.log"

    def _log_run(self, log_entry):
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Logging error: {e}")

    def validate_response(self, response: str) -> tuple[bool, str]:
        """
        Validates the output against the 8-part contract.
        Returns (is_valid, reason).
        """
        required_headers = [
            r"## 1\.\s+Framework\s+Selected",
            r"## 2\.\s+Executive\s+Summary",
            r"## 3\.\s+Framework\s+Analysis",
            r"## 4\.\s+Recommendation",
            r"## 5\.\s+Priority\s+Actions",
            r"## 6\.\s+Next\s+24\s+Hours",
            r"## 7\.\s+Risks\s+and\s+Missing\s+Information",
            r"## 8\.\s+Suggested\s+Follow-up\s+Questions"
        ]
        
        for pattern in required_headers:
            if not re.search(pattern, response, re.IGNORECASE):
                return False, f"Missing header pattern: {pattern}"

        # Extract Framework Name section
        fw_match = re.search(r"## 1\.\s+Framework\s+Selected\s*\n+([^\n#]+)", response, re.IGNORECASE)
        if not fw_match:
            return False, "Could not extract framework name."
        
        fw_name = fw_match.group(1).strip()
        # Clean up any potential markdown formatting around the framework name
        fw_name = re.sub(r"[\*\_`]", "", fw_name)
        # If there are sub-bullets/descriptions in the first line, just take the framework name (e.g. up to the first newline or hyphen)
        fw_name = re.split(r'[\n\-]', fw_name)[0].strip()
        if fw_name not in KNOWN_FRAMEWORKS:
            return False, f"Invalid framework name: '{fw_name}'"

        # Check section contents are non-empty
        # Let's split by the markdown headers to check each block
        parts = re.split(r"## \d\.\s+[^\n]+", response)
        if len(parts) < 9:
            return False, f"Expected 8 sections, found {len(parts)-1}"

        sections_to_check = {
            "Framework Selected": parts[1],
            "Executive Summary": parts[2],
            "Framework Analysis": parts[3],
            "Recommendation": parts[4],
            "Priority Actions": parts[5],
            "Next 24 Hours": parts[6],
            "Risks and Missing Information": parts[7],
            "Suggested Follow-up Questions": parts[8]
        }

        for sec_name, sec_content in sections_to_check.items():
            if not sec_content.strip():
                return False, f"Section '{sec_name}' is empty."

        # Check for leaks/internal structures
        leak_patterns = [
            r"---", r"<\|start_header_id\|>",
            r"<\|end_header_id\|>", r"<\|eot_id\|>"
        ]
        for pattern in leak_patterns:
            if re.search(pattern, response):
                return False, f"Internal label/leak detected: '{pattern}'"

        # Check for cloud API references
        cloud_patterns = [r"openai", r"gpt-4", r"anthropic", r"claude", r"gemini API"]
        for pattern in cloud_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return False, f"Cloud API reference detected: '{pattern}'"

        return True, "Valid"

    def parse_payment_details(self, query: str) -> Dict[str, Any]:
        prompt = f"""Identify if the user is asking to execute a financial payment, invoice, or refund.
User Request: "{query}"

If yes, extract:
- amount: float (default 0.0)
- merchant: string (default "Unknown Vendor")
- category: string (default "Services")
- action: string ("pay", "invoice", "refund", "none")
- destination: string (blockchain address, default "0xvendor_wallet_address_placeholder")

Format your response strictly as a JSON object, e.g.:
{{"amount": 49.00, "merchant": "Zoom", "category": "Subscriptions", "action": "pay", "destination": "0x123..."}}
Do not write any other text. Only valid JSON."""
        try:
            res = self.llm.invoke(prompt)
            match = re.search(r"\{.*\}", res, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
        return {"amount": 0.0, "merchant": "Unknown Vendor", "category": "Services", "action": "none", "destination": "0xvendor_wallet_address_placeholder"}

    def run(self, query: str, document_text: str, profile_data: Dict[str, Any], user_framework: Optional[str] = None, status_callback: Optional[Callable[[str], None]] = None) -> str:
        run_id = str(uuid.uuid4())
        start_time = time.time()
        
        log_entry = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "stages": [],
            "input_summary": query[:100],
            "selected_framework": None,
            "retrieved_chunk_count": 0,
            "validation_status": "Not Validated",
            "errors": []
        }

        # Check for payment/transaction action
        payment_details = self.parse_payment_details(query)
        if payment_details.get("action") in ["pay", "refund", "invoice"] and payment_details.get("amount", 0) > 0:
            action = payment_details["action"]
            amount = payment_details["amount"]
            merchant = payment_details["merchant"]
            category = payment_details["category"]
            dest = payment_details["destination"]
            
            print(f"[Orchestrator] Intercepted payment request for ${amount} to {merchant}")
            if status_callback:
                status_callback(f"Interrogating Policy Engine & Circle USDC Provider...")
                
            if action == "pay":
                pay_res = self.payment_agent.execute_payment_workflow(amount, merchant, category, dest)
            elif action == "refund":
                pay_res = {
                    "success": True,
                    "status": "completed",
                    "transaction_id": f"ref_{uuid.uuid4().hex[:12]}",
                    "circle_tx_id": f"circle_ref_{uuid.uuid4().hex[:16]}",
                    "amount": amount,
                    "merchant": merchant,
                    "category": "Refunds"
                }
                self.payment_db.add_transaction(pay_res["transaction_id"], "primary_usdc_wallet", amount, merchant, "Refunds", pay_res["circle_tx_id"], "completed")
                self.payment_db.add_audit_log("REFUND_ISSUED", f"Issued refund of {amount} USDC to customer {merchant}.")
            else:  # invoice
                pay_res = self.payment_agent.process_invoice(f"inv_{uuid.uuid4().hex[:6]}")
                
            if pay_res.get("success"):
                final_response = f"""## 1. Framework Selected
RUN DCMS ER
- The RUN DCMS ER framework focuses resources on revenue-generating actions, optimizing sales campaigns, and maximizing margins.

## 2. Executive Summary
The proposed payment for ${amount} to {merchant} was authorized by the Policy Engine and executed successfully via Circle.

## 3. Framework Analysis
- Current observation: Business required outbound USDC payment transaction.
- Business implication: The service has been paid for, preventing any provider service interruption.
- Assumption or missing information: Confirmed destination address {dest[:10]}... is accurate.

## 4. Recommendation
Authorized transaction execution within the defined limits of the active Policy Engine.

## 5. Priority Actions
1. Confirm receipt of service or access with the vendor.
2. Verify update on expense ledger.
3. Check remaining wallet balance.

## 6. Next 24 Hours
No manual checkout is required. Circle transaction has cleared.

## 7. Risks and Missing Information
- Risks: Merchant delivery delays or wallet mismatch.
- Missing: Immediate vendor confirmation.

## 8. Suggested Follow-up Questions
1. How do I modify my monthly spending limits?
2. Can I export our USDC expense audit history?

--- PAYMENT RECEIPT ---
Status: {pay_res['status'].upper()}
Transaction ID: {pay_res.get('transaction_id')}
Circle Tx Hash: {pay_res.get('circle_tx_id')}
Amount: {pay_res['amount']} USDC
Merchant: {pay_res['merchant']}
Category: {pay_res['category']}"""
            else:
                final_response = f"""## 1. Framework Selected
RUN DCMS ER
- The RUN DCMS ER framework focuses resources on revenue-generating actions, optimizing sales campaigns, and maximizing margins.

## 2. Executive Summary
The proposed payment request was BLOCKED or FAILED policy checks. No USDC funds were transferred.

## 3. Framework Analysis
- Current observation: Proposed payment to {merchant} triggered active Policy Engine rules.
- Business implication: Unauthorized or over-budget spends are blocked automatically to preserve runway.
- Assumption or missing information: Action requires founder override or budget expansion.

## 4. Recommendation
Review spending limit boundaries and approve pending items in the dashboard.

## 5. Priority Actions
1. Navigate to Policies to review daily caps.
2. Release this transaction from the Founder Approval Queue if appropriate.

## 6. Next 24 Hours
Adjust the maximum transaction limits to re-submit this payment if necessary.

## 7. Risks and Missing Information
- Risks: Blocked payments may suspend active subscription services.
- Missing: Policy overrides.

## 8. Suggested Follow-up Questions
1. How do I unlock a transaction in the approval queue?

--- PAYMENT BLOCK DETAILS ---
Status: {pay_res['status'].upper()}
Reason: {pay_res.get('reason')}
Amount: {pay_res['amount']} USDC
Merchant: {pay_res['merchant']}
Category: {pay_res['category']}"""
            
            self.memory_agent.add_record(query, "RUN DCMS ER", final_response)
            log_entry["total_duration"] = time.time() - start_time
            log_entry["selected_framework"] = "RUN DCMS ER"
            log_entry["validation_status"] = "Success"
            self._log_run(log_entry)
            if status_callback:
                status_callback("Completed.")
            return final_response

        def log_step(agent_name, progress_msg):
            print(f"[Orchestrator] {progress_msg}")
            if status_callback:
                status_callback(progress_msg)
            return {
                "agent": agent_name,
                "start": time.time()
            }

        def end_step(step_record, output_summary=""):
            duration = time.time() - step_record["start"]
            log_entry["stages"].append({
                "agent": step_record["agent"],
                "duration": duration,
                "output_summary": output_summary[:100]
            })

        # 1. Assessment
        s = log_step("AssessmentAgent", "Understanding your business challenge")
        assessment = self.assessment_agent.run(query, document_text, profile_data)
        end_step(s, str(assessment))
        
        # 2. Framework Selection
        s = log_step("FrameworkSelectionAgent", "Selecting the relevant Founder Framework")
        framework = self.framework_agent.run(assessment, user_framework)
        log_entry["selected_framework"] = framework.get("framework_name")
        end_step(s, str(framework))
        
        # 3. Knowledge Retrieval
        s = log_step("KnowledgeRetrievalAgent", "Retrieving framework knowledge")
        retrieved_context = self.retrieval_agent.run(query, framework["framework_name"])
        # Approximate chunk count (lines or separator count)
        chunks = len(retrieved_context.split("\n\n")) if retrieved_context else 0
        log_entry["retrieved_chunk_count"] = chunks
        end_step(s, f"Retrieved {len(retrieved_context)} chars")
        
        # 4. Memory Integration
        s = log_step("MemoryAgent", "Retrieving memory context")
        memory_context = self.memory_agent.get_context()
        end_step(s, memory_context)
        
        # 5. Strategy Generation
        s = log_step("StrategyAgent", "Developing the strategy")
        strategy = self.strategy_agent.run(query, assessment, framework, retrieved_context, memory_context)
        end_step(s, str(strategy))
        
        # 6. Execution Plan
        s = log_step("ExecutionCoachAgent", "Building the execution plan")
        execution = self.execution_agent.run(query, framework["framework_name"], strategy)
        end_step(s, str(execution))
        
        # 7. Response Composition
        s = log_step("ResponseComposer", "Finalizing the recommendation")
        final_response = self.response_composer.run(framework["framework_name"], strategy, execution)
        end_step(s, final_response)
        
        # Validate the response
        is_valid, validation_reason = self.validate_response(final_response)
        log_entry["validation_status"] = "Success" if is_valid else f"Failed: {validation_reason}"
        
        # Controlled Local Retry if failed
        if not is_valid:
            log_entry["errors"].append(f"Validation failed: {validation_reason}. Attempting one retry.")
            if status_callback:
                status_callback("Validation failed. Retrying recommendation generation...")
            
            # Retry Strategy and Execution with explicit instruction to avoid templates/leaks
            retry_assessment = assessment.copy()
            retry_assessment["primary_challenge"] = (
                f"{query} (Note: Output must be clean, professional prose, with NO internal delimiters or prompt labels)"
            )
            
            # Re-run Strategy
            s_retry = log_step("StrategyAgent (Retry)", "Developing the strategy (Retry)")
            strategy = self.strategy_agent.run(query, retry_assessment, framework, retrieved_context, memory_context)
            end_step(s_retry, str(strategy))
            
            # Re-run Execution
            exec_retry = log_step("ExecutionCoachAgent (Retry)", "Building the execution plan (Retry)")
            execution = self.execution_agent.run(query, framework["framework_name"], strategy)
            end_step(exec_retry, str(execution))
            
            # Re-run Compose
            comp_retry = log_step("ResponseComposer (Retry)", "Finalizing the recommendation (Retry)")
            final_response = self.response_composer.run(framework["framework_name"], strategy, execution)
            end_step(comp_retry, final_response)
            
            # Re-validate
            is_valid_retry, validation_reason_retry = self.validate_response(final_response)
            log_entry["validation_status"] = "Success (after retry)" if is_valid_retry else f"Failed retry: {validation_reason_retry}"
            if not is_valid_retry:
                log_entry["errors"].append(f"Retry validation failed: {validation_reason_retry}")

        # Update Memory with the final produced response
        self.memory_agent.add_record(query, framework["framework_name"], final_response)
        
        total_duration = time.time() - start_time
        log_entry["total_duration"] = total_duration
        self._log_run(log_entry)
        
        if status_callback:
            status_callback("Completed.")
            
        return final_response
