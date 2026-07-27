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
    log_file: str

    def __init__(self, llm: Any, vectorstore: Any) -> None:
        self.llm = llm
        self.vectorstore = vectorstore
        
        # Instantiate specialized agents
        self.assessment_agent = AssessmentAgent(llm)
        self.framework_agent = FrameworkSelectionAgent(llm)
        self.retrieval_agent = KnowledgeRetrievalAgent(vectorstore)
        self.strategy_agent = StrategyAgent(llm)
        self.execution_agent = ExecutionCoachAgent(llm)
        self.memory_agent = MemoryAgent()
        self.response_composer = ResponseComposer()
        
        self.log_file = "orchestrator.log"

    def _log_run(self, log_entry):
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Logging error: {e}")

    def validate_response(self, response: str) -> tuple[bool, str]:
        """
        Validates the output against the 7-part contract.
        Returns (is_valid, reason).
        """
        required_headers = [
            r"## 1\.\s+Business\s+Scenario",
            r"## 2\.\s+Framework\s+Name",
            r"## 3\.\s+Applied\s+Sections",
            r"## 4\.\s+Priority\s+Action",
            r"## 5\.\s+Dreamer",
            r"## 6\.\s+Guardian",
            r"## 7\.\s+Athlete"
        ]
        
        for pattern in required_headers:
            if not re.search(pattern, response, re.IGNORECASE):
                return False, f"Missing header pattern: {pattern}"

        # Extract Framework Name section
        fw_match = re.search(r"## 2\.\s+Framework\s+Name\s*\n+([^\n#]+)", response, re.IGNORECASE)
        if not fw_match:
            return False, "Could not extract framework name."
        
        fw_name = fw_match.group(1).strip()
        # Clean up any potential markdown formatting around the framework name
        fw_name = re.sub(r"[\*\_`]", "", fw_name)
        if fw_name not in KNOWN_FRAMEWORKS:
            return False, f"Invalid framework name: '{fw_name}'"

        # Check section contents are non-empty
        # Let's split by the markdown headers to check each block
        parts = re.split(r"## \d\.\s+[^\n]+", response)
        # parts[0] is before the first header, parts[1] is Scenario, etc.
        if len(parts) < 8:
            return False, f"Expected 7 sections, found {len(parts)-1}"

        sections_to_check = {
            "Scenario": parts[1],
            "Framework Name": parts[2],
            "Applied Sections": parts[3],
            "Priority Action": parts[4],
            "Dreamer": parts[5],
            "Guardian": parts[6],
            "Athlete": parts[7]
        }

        for sec_name, sec_content in sections_to_check.items():
            if not sec_content.strip():
                return False, f"Section '{sec_name}' is empty."

        # Check for leaks/internal structures
        leak_patterns = [
            r"---SCENARIO---", r"---APPLIED---", r"---DREAMER---", r"---GUARDIAN---",
            r"---PRIORITY---", r"---ATHLETE---", r"<\|start_header_id\|>",
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
