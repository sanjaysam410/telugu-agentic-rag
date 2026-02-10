import uuid
import re
from agentic_engine.agents.base_agent import BaseAgent
from agentic_engine.utils.telugu_utils import script_extraction
from agentic_engine.config import FEATURE_FLAGS, DEFAULT_AGENT_MODEL
from agentic_engine.llm_client import generate_json_response

class MetadataGenerationAgent(BaseAgent):
    """
    Agent 2: Metadata Generation.
    Extracts metadata from stories or prompts.
    """

    def __init__(self, config=None):
        super().__init__(agent_name="metadata_generation_agent", config=config)
        self.enabled = FEATURE_FLAGS.get("use_metadata_agent", False)
        self.genre_codes = [
            "FOLKLORE", "MYTHOLOGY", "MORAL_STORY", "CHILDREN_STORY",
            "COMEDY", "ADVENTURE", "MYSTERY", "SCIENCE", "ROMANCE",
            "PUZZLE", "POEM", "SONG", "SERIAL", "OTHER"
        ]

    def process(self, input_data: dict) -> dict:
        """
        input_data: {
            "source": "story" | "prompt",
            "text": str,
            "user_fields": dict (optional)
        }
        """
        if not self.enabled:
            return self.pass_through(input_data, reason="Feature flag disabled")

        source = input_data.get("source", "story")
        text = input_data.get("text", "")
        user_fields = input_data.get("user_fields", {})

        # --- Step 1: Script Extraction ---
        metadata = script_extraction(text)

        # Add basic identifiers
        metadata["language"] = user_fields.get("language", "Telugu")
        metadata["full_text"] = text  # Store complete source text
        if source == "story":
            metadata["story_id"] = str(uuid.uuid4())

        # Parse source reference
        if source_ref := user_fields.get("source_reference"):
            match = re.search(r'(\d{4})-(\d{2})', source_ref)
            if match:
                metadata["year"] = int(match.group(1))
                metadata["month"] = int(match.group(2))

        # Merge known user fields
        metadata.update(user_fields)

        # CHECK: Semantic fields
        has_semantic = all(k in user_fields for k in ["keywords", "genre", "theme"])

        # --- Step 2: LLM Extraction ---
        if not has_semantic:
            llm_metadata = self._extract_with_llm(
                text,
                source,
                user_fields.get("content_type", "STORY"),
                metadata["language"]
            )
            if llm_metadata:
                for k, v in llm_metadata.items():
                    if k not in metadata or not metadata[k]:
                         metadata[k] = v

        # Normalize Genre
        if metadata.get("genre"):
             metadata["normalized_genre_code"] = self._normalize_genre(metadata["genre"])

        return self.success(
            payload=metadata,
            meta={"source": source, "steps_completed": ["script", "llm"] if not has_semantic else ["script"]}
        )

    def _extract_with_llm(self, text: str, source: str, content_type: str, language: str = "Telugu") -> dict:
        """Call LLM to extract semantic metadata."""

        system_prompt = f"You are a {language} literature metadata extractor."
        truncated_text = text[:4000]

        user_prompt = f"""
        Analyze this {language} content and return a JSON object.

        IMPORTANT: All extracted values (summary, themes, morals) MUST be in {language} language.

        CONTENT TYPE: {content_type}
        SOURCE: {source}

        TEXT:
        {truncated_text}

        EXTRACT:
        1. title (string)
        2. keywords (list of strings, max 5)
        3. genre (string, in {language}. e.g. "జానపదం" for Folklore)
        4. theme (string, short)
        5. moral (string, if applicable)
        6. characters (list of strings)
        7. locations (list of strings)
        8. summary (string, 2 sentences)

        OUTPUT FORMAT (JSON only):
        {{
            "title": "...",
            "keywords": ["..."],
            "genre": "...",
            "theme": "...",
            "moral": "...",
            "characters": ["..."],
            "locations": ["..."],
            "summary": "..."
        }}
        """

        try:
            return generate_json_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=DEFAULT_AGENT_MODEL,
                max_tokens=2000,
                temperature=0.2
            )
        except Exception as e:
            return {}

    def _normalize_genre(self, genre_str: str) -> str:
        """Simple normalization."""
        if not genre_str: return "OTHER"
        genre_upper = genre_str.upper().replace(" ", "_")

        # Direct Code Match
        if genre_upper in self.genre_codes:
            return genre_upper

        # English substring match
        for code in self.genre_codes:
            if code in genre_upper:
                return code

        # Telugu/Localized Mapping
        # Map common Telugu terms to English codes
        mapping = {
            "జానపదం": "FOLKLORE",
            "పురాణం": "MYTHOLOGY",
            "ఐతిహ్యం": "MYTHOLOGY",
            "నీతి": "MORAL_STORY",
            "పిల్లల": "CHILDREN_STORY",
            "హాస్యం": "COMEDY",
            "సాహసం": "ADVENTURE",
            "రహస్యం": "MYSTERY",
            "విజ్ఞానం": "SCIENCE",
            "ప్రేమ": "ROMANCE",
            "పొడుపు": "PUZZLE",
            "గేయం": "POEM",
            "పాట": "SONG",
            "విశేషం": "OTHER"
        }

        for key, code in mapping.items():
            if key in genre_str:
                return code

        return "OTHER"
