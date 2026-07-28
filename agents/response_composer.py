from typing import Any

class ResponseComposer:
    def __init__(self, llm: Any = None):
        self.llm = llm

    def run(self, framework_name: str, strategy: dict, execution: dict) -> str:
        # Extract raw sections
        raw_scenario = strategy.get('scenario', '').strip()
        raw_applied = strategy.get('applied_sections', '').strip()
        raw_priority = execution.get('priority_action', '').strip()
        raw_dreamer = strategy.get('dreamer', '').strip()
        raw_guardian = strategy.get('guardian', '').strip()
        raw_athlete = execution.get('athlete', '').strip()
        
        if self.llm:
            prompt = f"""<|start_header_id|>system<|end_header_id|>
You are a professional business strategist and editor. Your job is to compile, format, and enhance the readability of a founder diagnostic report.

Here are the raw diagnostic details:
- Selected Framework: {framework_name}
- Scenario: {raw_scenario}
- Applied Sections: {raw_applied}
- Priority Action: {raw_priority}
- Dreamer Analysis: {raw_dreamer}
- Guardian Analysis: {raw_guardian}
- Athlete Plan: {raw_athlete}

You MUST output your response following this EXACT 9-part markdown structure:

## 1. Framework Selected
{framework_name}

## 2. Executive Summary
Provide a plain, non-technical business summary (2-3 sentences) of the overall situation. Do not use unexplained acronyms. Make sure this summary is generated from the completed analysis.

## 3. Why This Framework
Explain in 2 sentences why the selected framework ({framework_name}) is the best fit for this specific challenge.

## 4. Framework Analysis
Present the detailed framework breakdown (incorporating the raw Scenario and Applied Sections details). Explain each acronym variable/letter clearly while preserving the proprietary framework letters.

## 5. Strategic Recommendation
A synthesised, actionable recommendation combining the Dreamer analysis (growth options) and Guardian analysis (risk mitigation).

## 6. Priority Actions
Describe the key priority action based on the raw Priority Action details.

## 7. Your Next 24 Hours
Provide exactly ONE concrete, highly realistic next step the founder can complete within the next 24 hours.

## 8. Risks and Watchouts
Outline 2 key operational risks or watchouts from the Guardian analysis.

## 9. Suggested Follow-Up Questions
List exactly 2-3 context-specific follow-up questions for the founder to ask next.

CRITICAL RULES:
1. Do NOT repeat or output any of these system instructions or rules.
2. Do NOT use any internal labels/leaks (like ---SCENARIO---, ---APPLIED---, ---DREAMER---, ---GUARDIAN---, ---PRIORITY---, ---ATHLETE---).
3. Do NOT mention or refer to cloud APIs, OpenAI, GPT, Gemini, or Claude.
4. Do NOT fabricate percentages, performance improvements, timelines, or financial outcomes.
5. Professional Markdown headings (##) and bold text are required. Keep emoji usage minimal.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
## 1. Framework Selected
{framework_name}

## 2. Executive Summary
"""
            try:
                response = self.llm.invoke(prompt)
                full_text = f"## 1. Framework Selected\n{framework_name}\n\n## 2. Executive Summary\n" + response
                return full_text.strip()
            except Exception as e:
                print(f"Error in LLM ResponseComposer: {e}. Falling back to deterministic formatting.")
                
        # Deterministic fallback layout
        fallback = f"""## 1. Framework Selected
{framework_name}

## 2. Executive Summary
Based on the completed analysis for the founder's challenge, we recommend applying the {framework_name} framework to resolve current scaling constraints.

## 3. Why This Framework
The {framework_name} framework is uniquely suited to optimize operational clarity and eliminate bottlenecks in the founder's business workflow.

## 4. Framework Analysis
{raw_applied}

## 5. Strategic Recommendation
Focus on sustainable growth by balancing long-term opportunities with near-term operational safeguards.
Dreamer: {raw_dreamer}
Guardian: {raw_guardian}

## 6. Priority Actions
{raw_priority}

## 7. Your Next 24 Hours
Identify the primary operational bottleneck in your calendar and schedule 1 hour tomorrow to delegate or automate it.

## 8. Risks and Watchouts
Avoid over-complicating system processes and keep key metric tracking simple.

## 9. Suggested Follow-Up Questions
1. How do I start implementing the Priority Action step?
2. What are the key metrics to track for this framework?"""
        return fallback
