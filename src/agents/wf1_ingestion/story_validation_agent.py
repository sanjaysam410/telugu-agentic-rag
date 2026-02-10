
from typing import Dict, Any, List
import json
from src.agents.base import BaseAgent, AgentState
from src.utils.telugu_utils import script_validation
from src.config import Config

# --- State Definition ---
class ValidationState(AgentState):
    """
    State for the Validation Workflow.
    Requires: 'story_text', 'user_fields'
    """
    story_text: str
    user_fields: Dict[str, Any]
    validation_status: str = "pending"  # success, failure
    rejection_reason: str = None
    validation_meta: Dict[str, Any] = {}

class StoryValidationAgent(BaseAgent):
    """
    Workflow 1, Agent 1: Story Validation.
    Ensures only valid Telugu content enters the pipeline.
    """

    def __init__(self):
        super().__init__(name="StoryValidationAgent")
        self.enabled = Config.FEATURE_FLAGS.get("use_validator_agent", True)

    def run(self, state: ValidationState) -> ValidationState:
        """
        Main processing logic.
        """
        self.log_step("Start", "Validating story submission...")

        if not self.enabled:
            self.logger.warning("Validation Agent is disabled via feature flag.")
            state.validation_status = "skipped"
            return state

        story_text = state.story_text
        user_fields = state.user_fields

        # --- Step 0: Mandatory Field Check ---
        if not user_fields.get("title"):
             state.validation_status = "failure"
             state.rejection_reason = "Story Title is mandatory."
             state.errors.append("Missing Title")
             self.log_step("Validation", "Failed: Missing Title")
             return state

        # --- Step 1: Script Validation ---
        # Only validate Telugu script if language is Telugu (or unspecified default)
        language = user_fields.get("language", "Telugu")
        script_result = {}

        if language == "Telugu":
            script_result = script_validation(story_text)
            if not script_result["valid"]:
                state.validation_status = "failure"
                state.rejection_reason = script_result["reason"]
                state.errors.append(f"Script Validation Failed: {script_result['code']}")
                self.log_step("Validation", f"Failed: {script_result['reason']}")
                return state
        else:
            # Basic length check for other languages
            if len(story_text) < 50:
                 state.validation_status = "failure"
                 state.rejection_reason = "Story is too short."
                 state.errors.append("Script Validation Failed: TOO_SHORT")
                 self.log_step("Validation", "Failed: Story too short")
                 return state

        # --- Step 2: LLM Validation ---
        llm_result = self._validate_with_llm(story_text)

        state.validation_meta["llm_details"] = llm_result

        if not llm_result.get("overall_valid", False):
            state.validation_status = "failure"
            state.rejection_reason = llm_result.get("rejection_reason", "LLM rejected content")
            state.errors.append(f"LLM Rejection: {state.rejection_reason}")
            self.log_step("Validation", f"Failed: {state.rejection_reason}")
            return state

        # Success Match
        state.validation_status = "success"
        state.validation_meta["telugu_ratio"] = script_result.get("telugu_ratio")
        self.log_step("Success", "Story passed all validation checks.")

        return state

    def _validate_with_llm(self, story_text: str) -> dict:
        """Call LLM (Groq) to check coherence, narrative quality, and appropriateness."""

        system_prompt = """You are a strict Telugu content quality validator for a curated literary dataset.
This data will be used to train language models, so quality is CRITICAL.
You must ensure every accepted piece has genuine narrative or literary merit."""

        user_prompt = f"""
        Analyze this Telugu text for DATA QUALITY.

        TEXT:
        {story_text[:3000]}

        VALIDATION CRITERIA (check ALL):

        1. **COHERENCE**: Do sentences connect logically? Does one idea flow into the next?
           - Fantasy elements (magic, talking animals, gods) are FINE as long as the narrative is internally consistent.
           - REJECT if sentences are random, disconnected, or make no sense together.

        2. **MEANINGFULNESS**: Does the text convey a story, poem, song, article, or educational content?
           - REJECT if it is keyword stuffing, random word salad, or repeated phrases with no meaning.
           - REJECT if it reads like auto-generated filler text with no narrative purpose.

        3. **COMPLETENESS**: Does the text have some structure (beginning, middle, or end)?
           - Fragments or excerpts are OK if they are part of a coherent narrative.
           - REJECT if it is just a list of disconnected words or phrases pretending to be a story.

        4. **LANGUAGE QUALITY**: Is the Telugu natural and grammatically reasonable?
           - Minor errors are OK. Dialectal variations are OK.
           - REJECT if the Telugu is machine-garbled, nonsensical transliteration, or gibberish.

        5. **SAFETY**: Is it free from explicit hate speech, slurs, or harmful content?
           - Violence in a story context (e.g., battles, hunting) is ACCEPTABLE.
           - Explicit hate speech targeting communities is NOT acceptable.

        DECISION LOGIC:
        - If ALL 5 criteria pass → overall_valid: true
        - If ANY criterion fails → overall_valid: false, explain which and why

        OUTPUT FORMAT (JSON only):
        {{
            "is_coherent": true/false,
            "is_meaningful": true/false,
            "is_complete": true/false,
            "is_natural_telugu": true/false,
            "is_appropriate": true/false,
            "overall_valid": true/false,
            "rejection_reason": null or "specific reason"
        }}

        RETURN ONLY VALID JSON.
        """

        try:
            # Use generation_utils helper if possible, or direct call via config model
            # Here we reuse the pattern from RAG Agent for consistency
            from langchain_core.messages import SystemMessage, HumanMessage
            from src.config import get_reasoning_llm

            # Use the configured Validation Model (Groq)
            llm = get_reasoning_llm(temperature=0.1)

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = llm.invoke(messages)
            content = response.content

            # Parse JSON
            # Clean markdown code blocks if present
            cleaned_content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_content)

        except Exception as e:
            self.logger.error(f"LLM Validation Error: {e}")
            return {
                "overall_valid": False,
                "rejection_reason": f"LLM Validation Failed/Error: {str(e)}"
            }
