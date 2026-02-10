
import json
import uuid
import re
from typing import Dict, Any, List, Optional
from src.agents.base import BaseAgent, AgentState
from src.config import Config
from src.utils.telugu_utils import script_extraction
from langchain_core.messages import SystemMessage, HumanMessage

# --- State Definition ---
class MetadataState(AgentState):
    """
    State for the Metadata Generation Workflow.
    Requires: 'text', 'source_type' ('story'|'prompt'), 'user_fields'
    """
    text: str
    source_type: str = "story" # story or prompt
    user_fields: Dict[str, Any] = {}
    extracted_metadata: Dict[str, Any] = {}
    status: str = "pending"

class MetadataGenerationAgent(BaseAgent):
    """
    Workflow 1, Agent 2: Metadata Generation.
    Extracts metadata from stories or prompts using Script + LLM.
    """

    def __init__(self):
        super().__init__(name="MetadataGenerationAgent")
        self.enabled = Config.FEATURE_FLAGS.get("use_ingestion_agent", True) # Shared flag for now
        self.genre_codes = [
            "FOLKLORE", "MYTHOLOGY", "MORAL_STORY", "CHILDREN_STORY",
            "COMEDY", "ADVENTURE", "MYSTERY", "SCIENCE", "ROMANCE",
            "PUZZLE", "POEM", "SONG", "SERIAL", "OTHER"
        ]

    def run(self, state: MetadataState) -> MetadataState:
        """
        Executes metadata extraction.
        """
        self.log_step("Start", f"Extracting metadata for source: {state.source_type}")

        if not self.enabled:
             return state

        text = state.text
        user_fields = state.user_fields
        source = state.source_type

        # --- Step 1: Script Extraction ---
        metadata = script_extraction(text)

        # Add basic identifiers/user fields
        metadata["language"] = user_fields.get("language", "Telugu")
        metadata["full_text"] = text # Store complete source text if needed upstream, though IngestionAgent uses state.text

        if source == "story":
             # Use existing story_id if provided (e.g. re-run), else generate
             metadata["story_id"] = user_fields.get("story_id") or str(uuid.uuid4())

        # Parse source reference if provided by user
        if source_ref := user_fields.get("source_reference"):
             match = re.search(r'(\d{4})-(\d{2})', str(source_ref))
             if match:
                 metadata["year"] = int(match.group(1))
                 metadata["month"] = int(match.group(2))
        elif user_fields.get("source_year"):
             metadata["year"] = int(user_fields.get("source_year"))

        # Merge known user fields
        metadata.update(user_fields)

        # CHECK: Semantic fields presence
        # For prompts, we might only need keywords/genre. For stories, we need everything.
        required_semantic = ["keywords", "genre"]
        if source == "story":
             required_semantic.extend(["theme", "summary", "title"])

        has_all_semantic = all(k in user_fields for k in required_semantic)

        # --- Step 2: LLM Extraction ---
        if not has_all_semantic:
            self.log_step("LLM", "Extracting semantic metadata...")
            llm_metadata = self._extract_with_llm(
                text,
                source,
                user_fields.get("content_type", "STORY"),
                metadata.get("language", "Telugu")
            )

            if llm_metadata:
                for k, v in llm_metadata.items():
                    # Only overwrite if missing or empty in current metadata
                    if k not in metadata or not metadata[k]:
                         metadata[k] = v
        else:
            self.log_step("LLM", "Skipping LLM (All semantic fields provided)")

        # Normalization
        if metadata.get("genre"):
             metadata["normalized_genre_code"] = self._normalize_genre(metadata["genre"])

        # Update State
        state.extracted_metadata = metadata
        state.status = "success"
        self.log_step("Success", "Metadata extraction complete.")

        return state

    def _extract_with_llm(self, text: str, source: str, content_type: str, language: str = "Telugu") -> dict:
        """Call LLM to extract semantic metadata."""

        system_prompt = f"You are a {language} literature metadata extractor. Analyze the content and return JSON."
        truncated_text = text[:6000] # Increased context window slightly

        user_prompt = f"""
        Analyze this {language} content and return a JSON object.

        IMPORTANT: All extracted values (summary, themes, morals) MUST be in {language} language.

        CONTENT TYPE: {content_type}
        SOURCE: {source}

        TEXT:
        {truncated_text}

        EXTRACT THE FOLLOWING (If not explicitly provided):
        1. title (string) - Valid title for the story
        2. keywords (list of strings, max 5) - Key themes/subjects
        3. genre (string, in {language}. e.g. "జానపదం" for Folklore)
        4. theme (string, short)
        5. moral (string, if applicable/present)
        6. characters (list of strings)
        7. locations (list of strings)
        8. summary (string, 2 sentences)
        9. author (string, if mentioned/inferable, else null)
        10. year (integer, if mentioned/inferable, else null)
        11. source_reference (string, if mentioned, e.g. "Chandamama Oct 1980")

        OUTPUT FORMAT (JSON only):
        {{
            "title": "...",
            "keywords": ["..."],
            "genre": "...",
            "theme": "...",
            "moral": "...",
            "characters": ["..."],
            "locations": ["..."],
            "summary": "...",
            "author": "...",
            "year": 1990,
            "source_reference": "..."
        }}

        RETURN ONLY VALID JSON.
        """

        try:
            from src.config import get_reasoning_llm
            # Use Groq/Reasoning model
            llm = get_reasoning_llm(temperature=0.2)

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = llm.invoke(messages)
            content = response.content

            # Clean markdown
            cleaned_content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_content)

        except Exception as e:
            self.logger.error(f"Metadata LLM Error: {e}")
            return {}

    def _normalize_genre(self, genre_str: str) -> str:
        """Simple normalization mapping."""
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
