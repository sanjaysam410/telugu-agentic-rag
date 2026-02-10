import logging
import uuid
import os
from typing import Dict, Any, List
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

from src.agents.base import BaseAgent, AgentState
from src.config import Config

# --- State Definition ---
class IngestionState(AgentState):
    """
    State for the Ingestion Workflow.
    Requires: 'story_text', 'metadata', 'embedding_vector' (optional if computed here)
    """
    story_text: str
    metadata: Dict[str, Any]
    embedding_vector: List[float] = [] # Optional, if not pre-computed
    status: str = "pending"

class IngestionAgent(BaseAgent):
    """
    Workflow 1, Agent 3: Ingestion & Vectorization.

    Responsibility:
    1. Backup to MongoDB (Metadata + Content).
    2. Generate Embeddings (Alibaba GTE).
    3. Store in Qdrant (Vector DB).
    """

    def __init__(self):
        super().__init__(name="IngestionAgent")

        # 1. Initialize MongoDB Client
        try:
            if self.config.MONGO_URI:
                self.mongo_client = MongoClient(self.config.MONGO_URI)
                self.mongo_db = self.mongo_client[self.config.MONGO_DB_NAME]
                self.mongo_collection = self.mongo_db["stories"]
                self.logger.info(f"Connected to MongoDB: {self.config.MONGO_DB_NAME}")
            else:
                self.logger.warning("MONGO_URI missing. MongoDB backup will be skipped.")
                self.mongo_client = None
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            self.mongo_client = None

        # 2. Initialize Qdrant Client (Test Instance)
        qdrant_url = self.config.QDRANT_TEST_URL or self.config.QDRANT_URL
        qdrant_key = self.config.QDRANT_TEST_API_KEY or self.config.QDRANT_API_KEY

        if qdrant_url and qdrant_key:
            try:
                self.qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
                self.logger.info(f"Connected to Qdrant: {qdrant_url}")
            except Exception as e:
                self.logger.error(f"Failed to connect to Qdrant: {e}")
                self.qdrant_client = None
        else:
            self.logger.warning("Qdrant credentials missing. Vector storage will be skipped.")
            self.qdrant_client = None

        self.collection_name = "chandamama_stories"

        # 3. Initialize Embedding Model (Lazy Loading to save startup time)
        self.embedding_model = None

    def _load_model(self):
        if not self.embedding_model:
            self.logger.info(f"Loading Embedding Model: {self.config.STORY_EMBEDDING_MODEL_NAME}")
            self.embedding_model = SentenceTransformer(
                self.config.STORY_EMBEDDING_MODEL_NAME,
                trust_remote_code=True
            )

    def run(self, state: IngestionState) -> IngestionState:
        """
        Executes the ingestion pipeline.
        """
        title = state.metadata.get('title', 'Untitled')
        self.log_step("Start", f"Ingesting story: {title}")

        try:
            # 1. MongoDB Backup (Store everything "as is")
            if self.mongo_client:
                self._store_in_mongodb(state)

            # 2. Embedding Generation
            if not state.embedding_vector:
                self._generate_embedding(state)

            # 3. Qdrant Upsert
            if self.qdrant_client:
                self._store_in_qdrant(state)

            state.status = "success"
            self.log_step("Success", "Story ingested successfully.")

        except Exception as e:
            state.status = "failed"
            self.handle_error(e, state)

        return state

    def _store_in_mongodb(self, state: IngestionState):
        """Backup full payload to MongoDB."""
        self.log_step("MongoDB", "Backing up raw data...")

        # Prepare document
        document = {
            "story_id": state.metadata.get("story_id", str(uuid.uuid4())),
            "text": state.story_text,
            "metadata": state.metadata,
            "ingested_at": self._get_timestamp()
        }

        # Upsert based on story_id to prevent duplicates
        self.mongo_collection.update_one(
            {"story_id": document["story_id"]},
            {"$set": document},
            upsert=True
        )
        self.log_step("MongoDB", "Backup complete.")

    def _generate_embedding(self, state: IngestionState):
        """Generate embedding using Alibaba model."""
        self._load_model()
        self.log_step("Embedding", "Generating vector...")

        # Compose text to embed (Title + Keywords + Text snippet or Full Text)
        # For retrieval, usually we embed a rich representation
        text_to_embed = f"{state.metadata.get('title', '')} {state.metadata.get('keywords', '')} {state.story_text}"

        # Truncate if too long (simple check, ideally token based)
        text_to_embed = text_to_embed[:8000]

        embedding = self.embedding_model.encode(text_to_embed, normalize_embeddings=True)
        state.embedding_vector = embedding.tolist()

    def _store_in_qdrant(self, state: IngestionState):
        """Push vector to Qdrant."""
        self.log_step("Qdrant", f"Upserting to collection: {self.collection_name}")

        point_id = state.metadata.get("story_id") or str(uuid.uuid4())

        # Ensure ID is a valid UUID for Qdrant
        try:
            uuid.UUID(str(point_id))
        except ValueError:
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(point_id)))

        # STRICT WHITELISTING FOR QDRANT PAYLOAD
        # We only store fields relevant for retrieval and generation.
        # Everything else (raw metadata, OCR flags) is in MongoDB.
        whitelist_fields = [
            "text", "title", "keywords", "genre", "normalized_genre_code",
            "author", "locations", "characters", "moral", "year", "month"
        ]

        payload = {}

        # Always include text
        payload["text"] = state.story_text

        # Dynamically add other whitelisted fields if present in metadata
        for field in whitelist_fields:
            if field in state.metadata and state.metadata[field]:
                 payload[field] = state.metadata[field]

        # Explicit check for keywords/locations/characters to ensure they are lists
        for list_field in ["keywords", "locations", "characters"]:
            if list_field in payload and not isinstance(payload[list_field], list):
                 # Attempt to listify if it's a string
                 if isinstance(payload[list_field], str):
                      payload[list_field] = [x.strip() for x in payload[list_field].split(",")]

        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=[
                rest.PointStruct(
                    id=point_id,
                    vector=state.embedding_vector,
                    payload=payload
                )
            ]
        )

    def _get_timestamp(self):
        from datetime import datetime
        return datetime.utcnow().isoformat()
