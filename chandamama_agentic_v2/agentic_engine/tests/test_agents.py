import sys
import os
from unittest.mock import patch

# Ensure agentic_engine is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from agentic_engine.agents.story_validation_agent import StoryValidationAgent
from agentic_engine.agents.metadata_generation_agent import MetadataGenerationAgent

def test_validation_agent():
    print("\n--- Testing Story Validation Agent ---")
    agent = StoryValidationAgent()
    print(f"Agent Model (from Default): {agent.config.get('model', 'Not Set in Config, using Default')}")

    # Test 1: Invalid Script (Short/English) - Should fail as default language is Telugu
    res = agent.process({"story_text": "Short English text.", "user_fields": {"title": "Test Title"}})
    print(f"Invalid Script (Default Telugu) Status: {res['status']} (Expected: failure)")

    # Test 1.5: Valid English Script with Language=English
    english_story = "Once upon a time there was a king who ruled a great kingdom. " * 3
    res_english = agent.process({
        "story_text": english_story,
        "user_fields": {"title": "English Story", "language": "English"}
    })
    # This should pass script validation (skip Telugu check) and fail at LLM (mocked for Telugu) OR pass if we mock LLM generic
    # For now, let's see if it gets past script validation.
    print(f"English Script (Language=English) Status: {res_english['status']}")
    if res_english['status'] == 'failure':
         print(f"Reason: {res_english['error']['message']}")

    # Test 2: Missing Title
    res_missing = agent.process({"story_text": "అనగనగా ఒక రాజు. " * 20, "user_fields": {}})
    print(f"Missing Title Status: {res_missing['status']} (Expected: failure)")
    if res_missing['status'] == 'failure':
        print(f"Reason: {res_missing['error']['message']}")

    # Test 3: Valid Script + Title + Mock LLM
    valid_story = "అనగనగా ఒక రాజు. " * 20

    mock_response = {
        "is_coherent": True,
        "is_meaningful": True,
        "is_appropriate": True,
        "is_valuable": True,
        "overall_valid": True
    }

    # PATCH TARGET: The module where 'generate_json_response' is imported
    with patch('agentic_engine.agents.story_validation_agent.generate_json_response', return_value=mock_response):
        res = agent.process({"story_text": valid_story, "user_fields": {"title": "Valid Title"}})
        print(f"Valid Input Status: {res['status']} (Expected: success)")
        if res['status'] == 'success':
            print("Payload Keys:", res['payload'].keys())
        else:
            print("Error:", res.get('error'))

def test_metadata_agent():
    print("\n--- Testing Metadata Generation Agent ---")
    agent = MetadataGenerationAgent()

    # Test 1: Script Extraction + Semantic
    input_data = {
        "source": "story",
        "text": "అనగనగా ఒక రాజు. " * 5,
        "user_fields": {"genre": "Folklore"}
    }

    mock_response = {
        "title": "Test Story",
        "keywords": ["king"],
        "theme": "royalty",
        "genre": "Folklore",
        "characters": [],
        "locations": [],
        "summary": "Summary"
    }

    # PATCH TARGET: The module where 'generate_json_response' is imported
    with patch('agentic_engine.agents.metadata_generation_agent.generate_json_response', return_value=mock_response):
        res = agent.process(input_data)
        print(f"Status: {res['status']} (Expected: success)")
        if res['status'] == 'success':
            print("Metadata Keys:", res['payload'].keys())

    # Test 2: Metadata from Prompt
    print("\n[Metadata] Test 2: Prompt Input")
    prompt_input = {
        "source": "prompt",
        "text": "Write a story about a flying elephant.",
        "user_fields": {"keywords": ["magic", "elephant"]}
    }

    mock_prompt_response = {
         "title": "Flying Elephant",
         "genre": "FANTASY",
         "summary": "A magical elephant flies."
    }

    with patch('agentic_engine.agents.metadata_generation_agent.generate_json_response', return_value=mock_prompt_response):
        res = agent.process(prompt_input)
        print(f"Status: {res['status']} (Expected: success)")

    # Test 3: Metadata Language Propagation
    print("\n[Metadata] Test 3: Language Propagation (English)")
    english_input = {
        "source": "story",
        "text": "Once upon a time...",
        "user_fields": {"language": "English"}
    }
    # Mock response doesn't matter for this check, just need successful execution
    with patch('agentic_engine.agents.metadata_generation_agent.generate_json_response', return_value={}):
        res = agent.process(english_input)
        print(f"Status: {res['status']}")
        print(f"Language in Metadata: {res['payload'].get('language')} (Expected: English)")

if __name__ == "__main__":
    test_validation_agent()
    test_metadata_agent()
