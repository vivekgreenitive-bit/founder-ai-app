import json
import re

class AssessmentAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, query: str, document_text: str, profile_data: dict) -> dict:
        prompt = f"""<|start_header_id|>system<|end_header_id|>
You are an expert business analyst. Analyze the following startup details and output a clean JSON object containing the assessment. Do not include any explanation, markdown formatting outside of JSON, or other text.

IMPORTANT: You MUST extract the "stage" and "business_model" (industry) fields directly from the provided "Company Profile Context" below. Do not fabricate or default to SaaS if the profile specifies a different model (like Agency or Retail).

Company Profile Context:
{json.dumps(profile_data, indent=2)}

Uploaded Document Context:
{document_text[:1000]}

Founder's Query:
{query}

Respond ONLY with a valid JSON object matching this structure:
{{
  "stage": "extract stage from profile context",
  "business_model": "extract industry/model from profile context",
  "maturity": "maturity level",
  "primary_challenge": "detected primary challenge from query",
  "missing_info": ["info 1", "info 2"],
  "summary": "1 sentence scenario summary"
}}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
{{"""
        try:
            response = self.llm.invoke(prompt)
            # Ensure text starts with {
            text = response.strip()
            if not text.startswith("{"):
                text = "{" + text
            
            # Extract JSON from response text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
            return {
                "stage": profile_data.get("stage", "Unknown"),
                "business_model": profile_data.get("industry", "Unknown"),
                "maturity": "Unknown",
                "primary_challenge": query[:100],
                "missing_info": [],
                "summary": f"Analyzing: {query[:50]}"
            }
        except Exception as e:
            print(f"Error in AssessmentAgent: {e}")
            return {
                "stage": profile_data.get("stage", "Unknown"),
                "business_model": profile_data.get("industry", "Unknown"),
                "maturity": "Unknown",
                "primary_challenge": query[:100],
                "missing_info": [],
                "summary": f"Analyzing: {query[:50]}"
            }
