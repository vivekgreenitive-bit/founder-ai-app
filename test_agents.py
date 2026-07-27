import os
import sys

# Ensure current directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_engine import FounderAIEngine

def status_callback(status):
    print(f"🔄 [Status Update]: {status}")

def run_test():
    print("Initializing FounderAIEngine...")
    engine = FounderAIEngine()
    
    query = "How do I build a roadmap for next year?"
    print(f"\nRunning analysis for query: '{query}'")
    
    result = engine.analyze_query(query, status_callback=status_callback)
    
    print("\n" + "=" * 60)
    print("ANALYSIS RESULT:")
    print("=" * 60)
    print(result)
    print("=" * 60)

if __name__ == "__main__":
    run_test()
