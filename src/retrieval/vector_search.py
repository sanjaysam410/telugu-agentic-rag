from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from src.retrieval.client import get_qdrant_client
from src.config import Config

class StoryEmbeddingsRetriever:
    def __init__(self, top_k: int = 3):
        # We reuse the get_embedding_model from client or init here unique if needed.
        # The original code initialized SentenceTransformer directly here.
        print(f"Loading model '{Config.STORY_EMBEDDING_MODEL_NAME}' for Story Embeddings...")
        self.model = SentenceTransformer(Config.STORY_EMBEDDING_MODEL_NAME, trust_remote_code=True)

        print(f"Getting shared Qdrant client...")
        self.client = get_qdrant_client()
        self.top_k = top_k

    def retrieve_points(self, query: str):
        """
        Retrieves the raw ScoredPoints for top K similar FULL stories.
        """
        # Embed query with prefix as per original implementation
        query_text = f"query: {query}"
        query_vector = self.model.encode(query_text, normalize_embeddings=True)

        # Search
        search_results = self.client.query_points(
            collection_name=Config.STORY_COLLECTION_NAME,
            query=query_vector,
            limit=self.top_k,
            with_payload=True
        ).points
        return search_results

    def retrieve(self, query: str) -> str:
        """
        Retrieves the top K similar FULL stories as a formatted string.
        """
        search_results = self.retrieve_points(query)

        context_parts = []

        for i, hit in enumerate(search_results):
            payload = hit.payload

            title = payload.get("title", "Unknown Title")
            story_id = payload.get("story_id", hit.id)
            year = payload.get("year", "??")
            month = payload.get("month", "??")

            # The full text is stored in 'text' field of the payload
            text = payload.get("text", "")

            # Format nicely
            header = f"### Story {i+1}: {title} (ID: {story_id}, Date: {year}-{month})"
            context_parts.append(f"{header}\n\n{text}")

        return "\n\n".join(context_parts)
