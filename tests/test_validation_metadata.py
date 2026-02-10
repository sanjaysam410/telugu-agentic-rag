
import unittest
import sys
import os
from dotenv import load_dotenv

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.wf1_ingestion.story_validation_agent import StoryValidationAgent, ValidationState
from src.agents.wf1_ingestion.metadata_agent import MetadataGenerationAgent, MetadataState

# Load Env
load_dotenv()

class TestIngestionWorkflow(unittest.TestCase):

    def setUp(self):
        self.validator = StoryValidationAgent()
        self.metadata_miner = MetadataGenerationAgent()

        # Sample Telugu Story (Short)
        self.telugu_story = """
        అనగనగా ఒక రాజు. ఆ రాజు చాలా మంచివాడు.
        ప్రజలను కన్నబిడ్డల్లా చూసుకునేవాడు.
        ఒకరోజు ఒక ముసలివాడు సభకు వచ్చాడు.
        రాజు గారు అతనికి సహాయం చేశారు.
        నీతి: సహాయం చేయడం మానవ ధర్మం.
        """

        self.garbage_text = "sdfsdf sdfsdf sdfsdf 123l123"

    def test_validation_success(self):
        """Test validation agent with valid Telugu content."""
        print("\n--- Testing Validation Agent (Success Case) ---")
        state = ValidationState(
            story_text=self.telugu_story,
            user_fields={"title": "Test Story", "language": "Telugu"},
            messages=[],
            errors=[]
        )

        result = self.validator.run(state)

        print(f"Status: {result.validation_status}")
        if result.rejection_reason:
            print(f"Reason: {result.rejection_reason}")

        self.assertEqual(result.validation_status, "success")
        self.assertTrue(result.validation_meta.get("telugu_ratio", 0) > 50)

    def test_validation_failure_script(self):
        """Test validation agent with non-Telugu content."""
        print("\n--- Testing Validation Agent (Script Failure) ---")
        state = ValidationState(
            story_text=self.garbage_text,
            user_fields={"title": "Garbage", "language": "Telugu"},
            messages=[],
            errors=[]
        )

        result = self.validator.run(state)
        print(f"Status: {result.validation_status}")
        print(f"Reason: {result.rejection_reason}")

        self.assertEqual(result.validation_status, "failure")
        self.assertIn("No Telugu characters", result.rejection_reason)

    def test_metadata_extraction(self):
        """Test metadata extraction agent."""
        print("\n--- Testing Metadata Agent ---")
        state = MetadataState(
            text=self.telugu_story,
            source_type="story",
            user_fields={"title": "The Good King", "language": "Telugu"},
            messages=[],
            errors=[]
        )

        result = self.metadata_miner.run(state)
        meta = result.extracted_metadata

        print(f"Extracted Metadata Keys: {list(meta.keys())}")
        print(f"Genre: {meta.get('genre')}")
        print(f"Normalized Genre: {meta.get('normalized_genre_code')}")
        print(f"Summary: {meta.get('summary')}")

        # Check Script Stats
        self.assertIn("word_count", meta)
        self.assertIn("telugu_ratio", meta)

        # Check LLM extraction (if API key present, otherwise it might be empty but valid state)
        # We assume LLM is working if configured
        if meta.get("keywords"):
            self.assertIsInstance(meta["keywords"], list)

if __name__ == "__main__":
    unittest.main()
