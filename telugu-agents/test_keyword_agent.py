"""
Test script for Keyword Agent
Run with: python test_keyword_agent.py
"""
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import KeywordAgent
import json

def main():
    print("Testing Keyword Agent...")
    
    # Initialize agent
    agent = KeywordAgent()
    
    # Simulate story ingestion
    test_metadata = {
        "keywords": ["రాజు", "వినయం", "గర్వం"],
        "characters": ["రాజు", "మంత్రి"],
        "locations": ["రాజ్యం", "అడవి"],
        "normalized_genre_code": "MORAL_STORY",
        "author": "విశ్వం"
    }
    
    agent.on_story_ingested(test_metadata)
    agent.incremental_update()
    
    print("\n[SUCCESS] Stats after ingestion:")
    stats = agent.get_stats()
    
    # Write to file to avoid Windows console encoding issues
    with open("data/stats/test_output.json", "w", encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"[STATS] Stats written to data/stats/test_output.json")
    print(f"[INFO] Total keywords: {len(stats['keywords'])}")
    print(f"[INFO] Total stories: {stats['corpus_stats']['total_stories']}")
    print("\n[COMPLETE] Test completed successfully!")

if __name__ == "__main__":
    main()
