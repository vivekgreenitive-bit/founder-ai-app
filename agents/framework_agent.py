import re

class FrameworkSelectionAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, assessment: dict, user_selected_framework: str = None) -> dict:
        # If the user has selected a framework in the UI, use that as primary
        if user_selected_framework:
            match = re.search(r'(ECG KISS|SLR CAMERAS|MC BEERS|PC PEERS|PS ERP|DC ERPRS|OKS REC SME|PFA SAAS SME|RSS FEED SME|RPM REAP ER|RUN DCMS ER|ERM FABS ER|ADMINS ER)', user_selected_framework)
            if match:
                name = match.group(1)
                return {
                    "framework_name": name,
                    "confidence": 1.0,
                    "reasoning": "User manually selected this framework."
                }

        # Otherwise, ask the LLM to choose the best one
        prompt = f"""<|start_header_id|>system<|end_header_id|>
You are an expert business operations specialist. Based on the startup assessment, select the single best Founder Framework from this list:
- ECG KISS (Overall Business Diagnostic)
- SLR CAMERAS (Yearly Planning)
- MC BEERS (Quarterly Planning)
- PC PEERS (Monthly Planning)
- PS ERP (Weekly Planning)
- DC ERPRS (Daily Planning)
- OKS REC SME (Business System Architecture)
- PFA SAAS SME (Business Process Mapping)
- RSS FEED SME (SOP Builder)
- RPM REAP ER (Business Execution Strategy)
- RUN DCMS ER (Revenue Generation)
- ERM FABS ER (Business Evaluation)
- ADMINS ER (Crisis Management)

Startup Assessment:
{assessment}

Respond ONLY with the chosen framework's exact name from the list (e.g. 'OKS REC SME') followed by a short reason on the next line.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
        try:
            response = self.llm.invoke(prompt).strip()
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            framework_name = "ECG KISS"  # Default fallback
            reasoning = "Default framework selection."
            
            for f in ["ECG KISS", "SLR CAMERAS", "MC BEERS", "PC PEERS", "PS ERP", "DC ERPRS", "OKS REC SME", "PFA SAAS SME", "RSS FEED SME", "RPM REAP ER", "RUN DCMS ER", "ERM FABS ER", "ADMINS ER"]:
                if f in response:
                    framework_name = f
                    break
            if len(lines) > 1:
                reasoning = " ".join(lines[1:])
            elif lines:
                reasoning = lines[0]
                
            return {
                "framework_name": framework_name,
                "confidence": 0.8,
                "reasoning": reasoning
            }
        except Exception as e:
            print(f"Error in FrameworkSelectionAgent: {e}")
            return {
                "framework_name": "ECG KISS",
                "confidence": 0.5,
                "reasoning": f"Fallback due to error: {e}"
            }
