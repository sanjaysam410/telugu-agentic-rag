from agentic_engine.agents.base_agent import BaseAgent
from agentic_engine.utils.telugu_utils import script_validation
from agentic_engine.config import FEATURE_FLAGS, DEFAULT_AGENT_MODEL
from agentic_engine.llm_client import generate_json_response

class StoryValidationAgent(BaseAgent):
    """
    Agent 1: Story Validation.
    Ensures only valid Telugu content enters the pipeline.
    """

    def __init__(self, config=None):
        super().__init__(agent_name="story_validation_agent", config=config)
        self.enabled = FEATURE_FLAGS.get("use_validation_agent", False)

    def process(self, input_data: dict) -> dict:
        """
        Main processing logic.
        input_data: {"story_text": str, "user_fields": dict}
        """
        if not self.enabled:
            return self.pass_through(input_data, reason="Feature flag disabled")

        story_text = input_data.get("story_text", "")
        user_fields = input_data.get("user_fields", {})

        # --- Step 0: Mandatory Field Check ---
        if not user_fields.get("title"):
             return self.failure(
                error_code="MISSING_TITLE",
                message="Story Title is mandatory.",
                meta={"step": "pre_validation"}
            )

        # --- Step 1: Script Validation ---
        # Only validate Telugu script if language is Telugu (or unspecified default)
        language = user_fields.get("language", "Telugu")
        script_result = {}

        if language == "Telugu":
            script_result = script_validation(story_text)
            if not script_result["valid"]:
                return self.failure(
                    error_code=script_result["code"],
                    message=script_result["reason"],
                    meta={"step": "script"}
                )
        else:
            # Basic length check for other languages
            if len(story_text) < 50:
                 return self.failure(
                    error_code="TOO_SHORT",
                    message="Story is too short.",
                    meta={"step": "script"}
                )

        # --- Step 2: LLM Validation ---
        llm_result = self._validate_with_llm(story_text)

        if not llm_result.get("overall_valid", False):
            return self.failure(
                error_code="LLM_REJECTION",
                message=llm_result.get("rejection_reason", "LLM rejected content"),
                meta={"step": "llm", "llm_details": llm_result}
            )

        # Success Match
        return self.success(
            payload={
                "validated_story": story_text,
                "user_fields": input_data.get("user_fields", {})
            },
            meta={
                "telugu_ratio": script_result.get("telugu_ratio"),
                "validation_step": "llm_verified"
            }
        )

    def _validate_with_llm(self, story_text: str) -> dict:
        """Call LLM to check coherence and appropriateness."""

        system_prompt = "You are a content validator. Your job is to ACCEPT all Telugu content unless it is Gibberish, Spam, or Offensive."

        user_prompt = f"""
        Analyze this text.

        TEXT:
        {story_text[:3000]}

        INSTRUCTIONS:
        - The user is submitting valid cultural content (Poems, Songs, Stories, Lists).
        - ACCEPT IT if it is in Telugu script.
        - ACCEPT IT if it looks like lyrics or verses.
        - ONLY REJECT if it is absolute garbage, random characters, or explicit hate speech.

        QUESTIONS:
        1. Is this valid Telugu content? (True/False)
        2. Is it safe? (True/False)

        OUTPUT FORMAT (JSON only):
        {{
            "is_coherent": true,
            "is_meaningful": true,
            "is_appropriate": true,
            "is_valuable": true,
            "overall_valid": true,
            "rejection_reason": null
        }}

        If you must reject, set "overall_valid": false and provide a reason. BUT PREFER APPROVAL.
        """

        try:
            response = generate_json_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=DEFAULT_AGENT_MODEL,
                max_tokens=2000,
                temperature=0.1
            )
            return response
        except Exception as e:
            return {
                "overall_valid": False,
                "rejection_reason": f"LLM Validation Failed/Error: {str(e)}"
            }
