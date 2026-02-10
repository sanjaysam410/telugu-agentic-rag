"""
Run the Keyword Agent test
"""
if __name__ == "__main__":
    import json
    from keyword_agent import KeywordAgent
    
    # Simple test
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
    
    print("Stats after ingestion:")
    stats = agent.get_stats()
    
    # Write to file to avoid Windows console encoding issues
    with open("../data/stats/test_output.json", "w", encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"Stats written to data/stats/test_output.json")
    print(f"Total keywords: {len(stats['keywords'])}")
    print(f"Total stories: {stats['corpus_stats']['total_stories']}")
