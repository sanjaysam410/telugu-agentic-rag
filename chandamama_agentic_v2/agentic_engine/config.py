import os
from dotenv import load_dotenv

load_dotenv()

# Feature Flags for Agentic Rollout
FEATURE_FLAGS = {
    "use_validation_agent": True,
    "use_metadata_agent": True,
    "use_prompt_improvisation": True,
    "use_story_validation": True,
    "use_supabase_storage": False,
}

# LLM Configuration
LLM_MAX_TOKENS = 3000
LLM_TEMPERATURE = 0.7

# Map models to specific Environment Variable names for their API keys
MODEL_API_KEY_MAP = {

    "openai/gpt-oss-120b": "GROQ_API_KEY"
}

# Default Model for Agents
DEFAULT_AGENT_MODEL = "openai/gpt-oss-120b"
