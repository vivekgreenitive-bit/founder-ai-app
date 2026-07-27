class ExecutionCoachAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, query: str, framework_name: str, strategy: dict) -> dict:
        prompt = f"""<|start_header_id|>system<|end_header_id|>
You are Founder AI, an elite business execution coach. Given the business strategy analysis, generate the execution details.

Business Scenario: {strategy.get('scenario', '')}
Framework: {framework_name}
Applied Sections: {strategy.get('applied_sections', '')}

CRITICAL RULES:
1. Ground the priority action and athlete actions strictly in the Business Scenario above.
2. Do NOT copy template examples (e.g. do not mention casual wear, dress brands, sportswear, or real estate unless it is explicitly part of the Business Scenario above).

Generate:
1. A single high-impact priority action.
2. Three immediate, concrete actions for the athlete stage.

Format your output exactly as:
---PRIORITY---
[One high-impact action]
---ATHLETE---
[3 immediate execution actions, formatted as a numbered or bulleted list]
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
---PRIORITY---
"""
        try:
            response = self.llm.invoke(prompt)
            full_text = "---PRIORITY---\n" + response
            
            def clean_text(val):
                cleaned_lines = []
                for line in val.split("\n"):
                    if "---" in line and any(h in line.upper() for h in ["SCENARIO", "APPLIED", "DREAMER", "GUARDIAN", "PRIORITY", "ATHLETE"]):
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

            priority = extract_section(full_text, "PRIORITY", ["ATHLETE"])
            athlete = extract_section(full_text, "ATHLETE", [])
            
            return {
                "priority_action": priority,
                "athlete": athlete
            }
        except Exception as e:
            print(f"Error in ExecutionCoachAgent: {e}")
            return {
                "priority_action": "Execute immediate review of the process bottlenecks.",
                "athlete": "1. Schedule team meeting.\n2. Draft process map.\n3. Implement quick wins."
            }
