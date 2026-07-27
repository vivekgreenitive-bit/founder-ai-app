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
1. DO NOT copy the textbook business scenario from the Framework Reference Text. For example, if the reference text mentions "UK Biscuit Company", "Formal Dress Brand", or "Car Manufacturing", you MUST ignore those names and industries.
2. Ground your response entirely in the founder's actual problem ({query}) and their business model ({business_model}).
3. Translate the founder's problem ({query}) into a professional Business Scenario of 2-3 sentences.
4. Apply the framework's acronym variables directly to the founder's scenario. Do NOT copy the clothing, biscuit, or car examples from the reference. Write new examples custom to {business_model}.

Format your output exactly as:
---SCENARIO---
[Your Scenario text]
---APPLIED---
[Your Applied Sections text]
---DREAMER---
[Your Dreamer text]
---GUARDIAN---
[Your Guardian text]
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
