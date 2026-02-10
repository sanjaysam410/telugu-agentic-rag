"""
Test script for Prompt Agent
Run with: python test_prompt_agent.py
"""
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import PromptAgent
import json

def main():
    print("Testing Prompt Agent...")
    
    # Initialize agent
    agent = PromptAgent()
    
    # Test prompt
    result = agent.process_prompt(
        user_prompt="clever farmer",
        language="en",
        facets={"genre": "folk"}
    )
    
    print("\n[SUCCESS] Prompt optimization complete!")
    print(f"\n[ORIGINAL] {result['original_prompt']}")
    print(f"[TELUGU] {result['telugu_prompt']}")
    print(f"[EXPANSION] {result['expansion_applied']}")
    print(f"[FACETS] {', '.join(result['facets_integrated'])}")
    
    # Save to file
    with open("test_prompt_output.json", "w", encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n[SAVED] Full result saved to test_prompt_output.json")
    print("\n[COMPLETE] Test completed successfully!")

if __name__ == "__main__":
    main()
