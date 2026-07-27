class StrategyAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, query: str, assessment: dict, framework: dict, retrieved_context: str, memory_context: str) -> dict:
        prompt = f"""<|start_header_id|>system<|end_header_id|>
You are Founder AI, an elite business strategist. Given the business scenario details, analyze the situation and generate the strategic components of the diagnosis.

Business Scenario Details:
- Stage: {assessment.get('stage', 'N/A')}
- Business Model: {assessment.get('business_model', 'N/A')}
- Primary Challenge: {query}
- Framework selected: {framework.get('framework_name', 'N/A')}

Memory Context:
{memory_context}

Framework Reference Text (Context):
{retrieved_context}

STYLE: Business professional, elite consulting voice. Avoid generic MBA/SWOT advice.

Output three distinct sections:
1. **Business Scenario**: 2-3 sentences.
2. **Applied Sections**: 2-3 acronym applications with examples.
3. **Dreamer & Guardian Analysis**:
   - Dreamer: Growth opportunities.
   - Guardian: Risks and stability concerns.

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
