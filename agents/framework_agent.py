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
- ECG KISS (Use for: overall business diagnostics, idea-stage questions, product-market validation, initial setup)
- SLR CAMERAS (Use for: yearly planning and milestones)
- MC BEERS (Use for: quarterly planning, 90-day sprints)
- PC PEERS (Use for: monthly planning priorities)
- PS ERP (Use for: weekly sprint focus)
- DC ERPRS (Use for: daily planning, time management, prioritization overwhelm)
- OKS REC SME (Use for: delegation issues, removing founder as bottleneck, scaling system architecture)
- PFA SAAS SME (Use for: business process mapping, mapping delivery flows)
- RSS FEED SME (Use for: creating standard operating procedures (SOPs), team onboarding procedures)
- RPM REAP ER (Use for: team execution failure, lack of execution discipline, target accountability)
- RUN DCMS ER (Use for: low sales pipeline, revenue leaks, sales acceleration)
- ERM FABS ER (Use for: performance evaluation, assessing what is working/not working)
- ADMINS ER (Use for: active business crisis, severe cash flow runway warnings)

Startup Assessment:
{assessment}

Choose the single framework name that matches the challenge best.
Respond with the chosen framework's exact short name (e.g., 'ECG KISS') on the first line, followed by a short reason on the second line. Do not include any other markdown formatting.
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
