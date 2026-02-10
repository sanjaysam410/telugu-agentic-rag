import os
import logging
import random
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """
    Central configuration for the Agentic RAG system.
    Supports API Key Rotation for Google Gemini to handle rate limits.
    """

    # --- Feature Flags ---
    FEATURE_FLAGS = {
        "use_ingestion_agent": True,
        "use_rag_agent": True,
        "use_validator_agent": True,
    }

    # --- API Keys & Endpoints ---
    # Gemini (Language Engine) - Supports Rotation
    # Parsing: 'key1,key2,key3'
    _google_keys_str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_API_KEYS = [k.strip() for k in _google_keys_str.split(",") if k.strip()]

    # Legacy single key access (returns first key available)
    GOOGLE_API_KEY = GOOGLE_API_KEYS[0] if GOOGLE_API_KEYS else None

    # GPT-OSS (Reasoning Engine) - via Groq, Together, etc.
    # We use the OpenAI Client but point it to Groq's endpoint.
    OPENAI_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")

    # Vector DB
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

    # Qdrant Test Instance
    QDRANT_TEST_URL = os.getenv("QDRANT_TEST_URL", "https://a49d8967-5aa6-40d0-b9dd-736f3ab29155.europe-west3-0.gcp.cloud.qdrant.io")
    QDRANT_TEST_API_KEY = os.getenv("QDRANT_TEST_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.Fn7BzZHNERMYCH8r8yYGf1ZXN-5iRubZfS6thiYsrlw")

    # MongoDB (Metadata & Backup)
    MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://divyanshtejaedla_db_user:0NSf0GRs28WdAIT0@telugu-stories-cluster.6zt08v2.mongodb.net/?appName=Telugu-stories-cluster")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "chandamama_rag")

    # Storage
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # --- Model Selection (Hybrid Strategy) ---

    # 1. Reasoning Model (GPT-OSS 120B)
    # Recommended Groq Models: "openai/gpt-oss-120b"
    REASONING_MODEL_NAME = os.getenv("REASONING_MODEL_NAME", "openai/gpt-oss-120b")

    # 2. Language Model (Gemini)
    # Used for: Telugu Translation, Polish, Grammar
    LANGUAGE_MODEL_NAME = os.getenv("LANGUAGE_MODEL_NAME", "models/gemini-2.5-flash-lite")

    # --- Agent-Specific Models ---
    # Validation Agent (Needs high logic/safety) -> Groq/Reasoning
    VALIDATION_MODEL = REASONING_MODEL_NAME

    # Metadata Agent (Needs extraction/formatting) -> Groq/Reasoning
    METADATA_EXTRACTOR_MODEL = REASONING_MODEL_NAME

    # --- Retrieval Configuration ---
    # Qdrant Mode (Cloud vs Local)
    # If URL and Key are set, default to cloud. Otherwise local.
    QDRANT_MODE = "cloud" if (QDRANT_URL and QDRANT_API_KEY) else "local"
    QDRANT_PATH = QDRANT_URL if QDRANT_MODE == "cloud" else os.path.join(os.getcwd(), "qdrant_db")

    # Collections & Models
    STORY_COLLECTION_NAME = "chandamama_stories"
    STORY_EMBEDDING_MODEL_NAME = "Alibaba-NLP/gte-multilingual-base"

    # Search Settings
    TOP_K_RETRIEVAL = 2

    # UI / Stats
    STATS_PATH = "data/stats/global_stats.json"

    @classmethod
    def validate(cls):
        """Ensure critical env vars are set."""
        required = []
        if cls.FEATURE_FLAGS["use_rag_agent"] or cls.FEATURE_FLAGS["use_validator_agent"]:
             # We need LLMs for these
             if not cls.GOOGLE_API_KEYS: required.append("GOOGLE_API_KEY")
             if not cls.OPENAI_API_KEY: required.append("OPENAI_API_KEY")

        if cls.FEATURE_FLAGS["use_ingestion_agent"] or cls.FEATURE_FLAGS["use_rag_agent"]:
            if not cls.QDRANT_URL: required.append("QDRANT_URL")

        if required:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(required)}")

# --- Model Factories ---

def get_reasoning_llm(temperature: float = 1.0):
    """
    Returns the Reasoning Engine (GPT-OSS).
    Strictly for logic, validation, and structure.
    """
    if not Config.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set. Reasoning LLM may fail.")

    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=Config.REASONING_MODEL_NAME,
        temperature=temperature,
        api_key=Config.OPENAI_API_KEY,
        base_url=Config.OPENAI_BASE_URL,
        max_retries=2,
        model_kwargs={"reasoning_effort": "medium"}
    )

def get_language_llm(temperature: float = 0.3):
    """
    Returns the Language Engine (Gemini).
    Strictly for Telugu translation, polishing, and fluency.
    Implements random API Key Rotation for load balancing.
    """
    if not Config.GOOGLE_API_KEYS:
        logger.warning("GOOGLE_API_KEY not set. Language LLM may fail.")
        selected_key = None
    else:
        selected_key = random.choice(Config.GOOGLE_API_KEYS)
        # logger.info(f"Using Google API Key: ...{selected_key[-4:] if selected_key else 'None'}")

    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=Config.LANGUAGE_MODEL_NAME,
        temperature=temperature,
        google_api_key=selected_key,
        convert_system_message_to_human=True # Gemini quirk
    )
