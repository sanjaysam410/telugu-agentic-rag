
import os
import sys
import unittest
import uuid
from dotenv import load_dotenv

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.wf1_ingestion.ingestion_agent import IngestionAgent, IngestionState
from src.config import Config

# Load Env
load_dotenv()

class TestIngestionAgent(unittest.TestCase):

    def setUp(self):
        self.agent = IngestionAgent()
        self.mock_story = {
            "story_id": "test-story-watchlist-001",
            "title": "Test Story: The Whitelist Verification",
            "text": "This story tests if we properly filter metadata.",
            "keywords": ["test", "whitelist"],
            "genre": "Test",
            # Fields that SHOULD appear in Qdrant
            "author": "Tester",
            "characters": ["Bot A", "Bot B"],
            "locations": ["Server Room"],
            "moral": "Always filter inputs",
            "year": 2025,
            # Fields that SHOULD NOT appear in Qdrant (Junk/System)
            "ocr_confidence": 0.99,
            "processing_time_ms": 120,
            "system_flag_x": True,
            "raw_file_path": "/tmp/xyz.txt"
        }

    def test_ingestion_flow_whitelist(self):
        """Test the full ingestion flow with strict whitelisting check."""
        print("\n--- Testing Ingestion Flow (Whitelist Check) ---")

        # 1. Prepare State
        state = IngestionState(
            story_text=self.mock_story["text"],
            metadata=self.mock_story,
            messages=[],
            errors=[]
        )

        # 2. Run Agent
        result = self.agent.run(state)
        self.assertEqual(result.status, "success")

        # 3. Verify Qdrant Payload
        if self.agent.qdrant_client:
            # Get Point ID
            try:
                uuid.UUID(self.mock_story["story_id"])
                point_id = self.mock_story["story_id"]
            except:
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, self.mock_story["story_id"]))

            points = self.agent.qdrant_client.retrieve(
                collection_name=self.agent.collection_name,
                ids=[point_id]
            )
            self.assertTrue(len(points) > 0)
            payload = points[0].payload

            print(f"Qdrant Payload Keys: {list(payload.keys())}")

            # ASSERTIONS
            # Whitelisted fields MUST be present
            self.assertIn("title", payload)
            self.assertIn("author", payload)
            self.assertIn("moral", payload)
            self.assertIn("year", payload)
            self.assertIn("characters", payload)

            # Junk fields MUST be absent
            self.assertNotIn("ocr_confidence", payload)
            self.assertNotIn("processing_time_ms", payload)
            self.assertNotIn("system_flag_x", payload)

            print("Verified: Qdrant payload contains ONLY whitelisted fields.")
        else:
            print("Skipped: Qdrant verification (Client not initialized).")

if __name__ == "__main__":
    unittest.main()
