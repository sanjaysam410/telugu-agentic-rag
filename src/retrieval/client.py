import os
import sys
import uuid
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from src.config import Config

_client_instance = None
_model_instance = None

def get_qdrant_client():
    global _client_instance
    if _client_instance is None:
        if Config.QDRANT_MODE == "cloud":
            print(f"Connecting to Qdrant Cloud at {Config.QDRANT_URL}...", flush=True)
            _client_instance = QdrantClient(
                url=Config.QDRANT_URL,
                api_key=Config.QDRANT_API_KEY
            )
        else:
            # Local Mode
            if not os.path.exists(Config.QDRANT_PATH):
                 # In agentic mode, we might not want to raise error immediately but let it try or fail gracefully
                 print(f"WARNING: Qdrant DB not found at {Config.QDRANT_PATH}.", flush=True)
            print(f"Connecting to Local Qdrant at {Config.QDRANT_PATH}...", flush=True)
            _client_instance = QdrantClient(path=Config.QDRANT_PATH)
    return _client_instance

def get_embedding_model():
    global _model_instance
    if _model_instance is None:
        # Use story embedding model as default for RAG agent context if not specified otherwise
        # But generally we might need specific models. Config has STORY_EMBEDDING_MODEL_NAME.
        model_name = Config.STORY_EMBEDDING_MODEL_NAME
        print(f"Loading embedding model '{model_name}'...", flush=True)
        # trust_remote_code=True needed for Alibaba GTE
        _model_instance = SentenceTransformer(model_name, trust_remote_code=True)
    return _model_instance

def get_embedding(text: str):
    model = get_embedding_model()
    # Alibaba GTE / E5 usually need prefixes?
    # The original vector_search.py used "query: " prefix.
    # We will let the caller handle prefixes or standardize here.
    # For now, keeping simple encode.
    return model.encode(text, normalize_embeddings=True)
