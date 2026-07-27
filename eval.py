import os
import time
import sys

# Try to import llama_cpp
try:
    from llama_cpp import Llama
except ImportError:
    print("Error: llama-cpp-python is required to run the evaluation.")
    print("Install it with: pip install llama-cpp-python")
    sys.exit(1)

# Model Settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATHS = [
    os.path.join(BASE_DIR, "models", "unsloth.Q8_0.gguf"),
    os.path.join(BASE_DIR, "models", "unsloth.Q4_K_M.gguf"),
    os.path.join(BASE_DIR, "unsloth.Q8_0.gguf"),
    os.path.join(BASE_DIR, "unsloth.Q4_K_M.gguf"),
    os.path.join(BASE_DIR, "models", "Llama-3.2-3B-Instruct-Q4_K_M.gguf") # fallback
]

# Evals Test Cases (Input Question -> Expected Keyword to verify factual recall)
TEST_CASES = [
    {
        "q": "What does the SLR CAMERAS framework stand for?",
        "keyword": "Success Peak",
        "framework": "SLR CAMERAS"
    },
    {
        "q": "Explain the ECG KISS framework.",
        "keyword": "End Goal",
        "framework": "ECG KISS"
    },
    {
        "q": "How does a founder prevent burnout using systems?",
        "keyword": "OKS REC SME",
        "framework": "OKS REC SME"
    },
    {
        "q": "What is the 90-day execution framework?",
        "keyword": "MC BEERS",
        "framework": "MC BEERS"
    },
    {
        "q": "How to handle a sudden operational crisis or failure?",
        "keyword": "ADMINS ER",
        "framework": "ADMINS ER"
    }
]

def run_evaluation():
    # 1. Locate Model
    model_path = None
    for path in MODEL_PATHS:
        if os.path.exists(path):
            model_path = path
            break
            
    if not model_path:
        print("❌ Error: No GGUF model found in the project. Please place your fine-tuned GGUF file in the app directory.")
        return

    print(f"📦 Loading model: {model_path}...")
    try:
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            temperature=0.1,
            verbose=False
        )
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return

    print("\n🚀 Starting LLM Evaluation Suite...")
    print("=" * 60)
    
    passed_facts = 0
    passed_structure = 0
    total_cases = len(TEST_CASES)

    for i, case in enumerate(TEST_CASES, 1):
        print(f"\n📝 Test Case {i}/{total_cases}: {case['q']}")
        
        # Format the instruction with standard chat template format
        prompt = f"""<|start_header_id|>system<|end_header_id|>
You are Founder AI, an elite business consultant. Output strictly using the 7-part template.

## STRICT OUTPUT TEMPLATE (MANDATORY)
## 1. Business Scenario
## 2. Framework Name
## 3. Applied Sections
## 4. Priority Action
## 5. Dreamer
## 6. Guardian
## 7. Athlete
<|eot_id|><|start_header_id|>user<|end_header_id|>
{case['q']}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
## 1. Business Scenario"""

        start_time = time.time()
        output = llm(prompt, max_tokens=1000, stop=["<|eot_id|>"])
        elapsed = time.time() - start_time
        
        response_text = "## 1. Business Scenario" + output["choices"][0]["text"]
        token_count = len(response_text.split())
        tokens_per_sec = token_count / elapsed if elapsed > 0 else 0

        # Eval 1: Factual Acronym Recall
        fact_check = case['keyword'].lower() in response_text.lower() or case['framework'].lower() in response_text.lower()
        if fact_check:
            passed_facts += 1
            fact_status = "✅ PASSED (Recalled framework data)"
        else:
            fact_status = f"❌ FAILED (Could not find reference to '{case['keyword']}')"

        # Eval 2: Structural Verification (Does it output the 7 parts?)
        required_headers = [
            "## 1. Business Scenario",
            "## 2. Framework Name",
            "## 3. Applied Sections",
            "## 4. Priority Action",
            "## 5. Dreamer",
            "## 6. Guardian",
            "## 7. Athlete"
        ]
        
        structure_check = all(header in response_text for header in required_headers)
        if structure_check:
            passed_structure += 1
            structure_status = "✅ PASSED (Structured output matches PyQt parser)"
        else:
            structure_status = "❌ FAILED (Mismatch in 7-part template headers)"

        print(f"⏱️  Time taken: {elapsed:.2f}s | Speed: {tokens_per_sec:.1f} tokens/sec")
        print(f"📊 Facts Recall: {fact_status}")
        print(f"🏗️  Structure:    {structure_status}")

    print("\n" + "=" * 60)
    print("📈 FINAL EVALUATION REPORT")
    print("-" * 60)
    print(f"Model tested:      {os.path.basename(model_path)}")
    print(f"Factual Accuracy:  {passed_facts}/{total_cases} ({ (passed_facts/total_cases)*100 :.1f}%)")
    print(f"UI Parser Check:   {passed_structure}/{total_cases} ({ (passed_structure/total_cases)*100 :.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    run_evaluation()
