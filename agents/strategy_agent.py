from typing import Any, Dict

class StrategyAgent:
    llm: Any

    def __init__(self, llm: Any) -> None:
        self.llm = llm

    def run(self, query: str, assessment: Dict[str, Any], framework: Dict[str, Any], retrieved_context: str, memory_context: str) -> Dict[str, Any]:
        stage = assessment.get('stage', 'N/A')
        business_model = assessment.get('business_model', 'N/A')
        framework_name = framework.get('framework_name', 'N/A')
        
        prompt = f"""<|start_header_id|>system<|end_header_id|>
You are Founder AI, an elite business strategist. Solve the founder's challenge using the provided framework context.

[FOUNDER DETAILS]
- Stage: {stage}
- Business Model/Industry: {business_model}
- Current Problem: {query}
- Selected Framework: {framework_name}

[CONVERSATION MEMORY]
{memory_context}

[FRAMEWORK REFERENCE TEXT]
{retrieved_context}

[CRITICAL INSTRUCTIONS]
1. DO NOT copy the textbook business scenario from the Framework Reference Text.
2. Ground your response entirely in the founder's actual problem ({query}) and their business model ({business_model}).
3. For the Scenario text: Directly answer the founder's question in less than 120 words. Do not repeat the input or write generic text.
4. For the Applied Sections: For each relevant framework component/variable, write a concise breakdown structured as:
   - Current observation: [brief observation]
   - Business implication: [brief implication]
   - Assumption or missing information: [brief assumption/missing info]
5. Retrieve principles from reference text and apply them to user context; do not copy book paragraphs, examples, or definitions verbatim. Do not invent revenue, costs, percentages, or timelines.

Format your output exactly as:
---SCENARIO---
[Your direct answer Executive Summary text]
---APPLIED---
[Your Applied Sections text]
---DREAMER---
[Your Dreamer growth opportunities text]
---GUARDIAN---
[Exactly: Max 2 operational risks, and Max 3 missing data points or assumptions]
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
---SCENARIO---
"""
        try:
            response = self.llm.invoke(prompt)
            full_text = "---SCENARIO---\n" + response
            
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

            scenario = extract_section(full_text, "SCENARIO", ["APPLIED", "DREAMER", "GUARDIAN"])
            applied = extract_section(full_text, "APPLIED", ["DREAMER", "GUARDIAN"])
            dreamer = extract_section(full_text, "DREAMER", ["GUARDIAN"])
            guardian = extract_section(full_text, "GUARDIAN", [])
            
            return {
                "scenario": scenario,
                "applied_sections": applied,
                "dreamer": dreamer,
                "guardian": guardian
            }
        except Exception as e:
            print(f"Error in StrategyAgent: {e}")
            return {
                "scenario": f"The founder is addressing a challenge with the {framework.get('framework_name')} framework.",
                "applied_sections": f"Applying the {framework.get('framework_name')} steps directly to the issue.",
                "dreamer": "Growth and acceleration options.",
                "guardian": "Risk mitigations and operational safeguards."
            }
