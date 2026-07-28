from typing import Any, Dict

class ExecutionCoachAgent:
    llm: Any

    def __init__(self, llm: Any) -> None:
        self.llm = llm

    def run(self, query: str, framework_name: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""<|start_header_id|>system<|end_header_id|>
You are Founder AI, an elite business execution coach. Given the business strategy analysis, generate the execution details.

Business Scenario: {strategy.get('scenario', '')}
Framework: {framework_name}
Applied Sections: {strategy.get('applied_sections', '')}
Dreamer Focus: {strategy.get('dreamer', '')}
Guardian Focus: {strategy.get('guardian', '')}

CRITICAL RULES:
1. State the recommended decision clearly, explain why, and mention one alternative and why it is not preferred.
2. Provide maximum three concrete, measurable priority actions.
3. Provide exactly one action for the next 24 hours that takes less than two hours to complete.
4. Do NOT copy template examples verbatim from instructions or database reference.
5. Do NOT invent revenue, costs, percentages, or ROI.

Format your output exactly as:
---RECOMMENDATION---
[Recommended decision, why, alternative, and why not preferred]
---PRIORITY---
[Maximum three concrete, measurable actions]
---NEXT24H---
[Exactly one action taking less than 2 hours]
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
---RECOMMENDATION---
"""
        try:
            response = self.llm.invoke(prompt)
            full_text = "---RECOMMENDATION---\n" + response
            
            def clean_text(val):
                cleaned_lines = []
                for line in val.split("\n"):
                    if "---" in line and any(h in line.upper() for h in ["SCENARIO", "APPLIED", "DREAMER", "GUARDIAN", "RECOMMENDATION", "PRIORITY", "NEXT24H"]):
                        continue
                    cleaned_lines.append(line)
                return "\n".join(cleaned_lines).strip()

            def extract_section(text, header, next_headers):
                try:
                    start_idx = text.find(f"---{header}---")
                    if start_idx == -1:
                        start_idx = text.lower().find(f"---{header.lower()}---")
                    if start_idx == -1:
                        return ""
                    start_idx += len(f"---{header}---")
                    
                    end_idx = len(text)
                    for nh in next_headers:
                        nh_idx = text.find(f"---{nh}---")
                        if nh_idx == -1:
                            nh_idx = text.lower().find(f"---{nh.lower()}---")
                        if nh_idx != -1 and nh_idx > start_idx:
                            end_idx = min(end_idx, nh_idx)
                            
                    return clean_text(text[start_idx:end_idx])
                except Exception as e:
                    print(f"Error extracting section {header}: {e}")
                    return ""

            recommendation = extract_section(full_text, "RECOMMENDATION", ["PRIORITY", "NEXT24H"])
            priority = extract_section(full_text, "PRIORITY", ["NEXT24H"])
            next24 = extract_section(full_text, "NEXT24H", [])
            
            return {
                "recommendation": recommendation,
                "priority_action": priority,
                "athlete": next24
            }
        except Exception as e:
            print(f"Error in ExecutionCoachAgent: {e}")
            return {
                "recommendation": "We recommend focus on standardizing primary workflows before committing capital to expansion. Alternative of immediate expansion carries high overhead.",
                "priority_action": "1. Audit current capacity bottleneck.\n2. Document team role limits.\n3. Implement target KPI tracking.",
                "athlete": "Record a 5-minute screencast documenting your core delivery process today."
            }
