import json
import logging
import time
import os
from typing import Dict, List, Optional, Any
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from utils.telugu_utils import is_telugu, count_telugu_chars, extract_keywords

class PromptAgentConfig:
    LLM_TIMEOUT_SECONDS = 30
    MAX_RETRIES = 2
    MIN_TELUGU_RATIO = 0.5
    MAX_EXPANSION_RATIO = 3.0
    SUPPORTED_LANGUAGES = ["te", "en", "hi", "ta", "kn", "ml"]
    # Ideally load this from environment variables
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyAuNLT8ZhTIhok-b-rJlHboYP3FOKAmzNE")

class PromptAgent:
    def __init__(self, config: PromptAgentConfig = PromptAgentConfig()):
        self.config = config
        genai.configure(api_key=self.config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def _call_llm(self, prompt: str) -> str:
        """
        Call Gemini API.
        """
        logger.info(f"Calling Gemini LLM with prompt length: {len(prompt)}...")

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise e

    def process_prompt(self, user_prompt: str, language: str, facets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the user prompt to generate an optimized Telugu prompt.
        """
        logger.info(f"Processing prompt: {user_prompt}, Language: {language}")

        # 1. Validation
        if not user_prompt:
            raise ValueError("User prompt cannot be empty.")

        # 2. Construct LLM Prompt
        llm_system_prompt = self._construct_system_prompt(user_prompt, language, facets)

        # 3. Call LLM with retries
        llm_output = ""
        for attempt in range(self.config.MAX_RETRIES + 1):
            try:
                llm_output = self._call_llm(llm_system_prompt)
                if self._validate_output(llm_output):
                    break
                else:
                    logger.warning(f"Attempt {attempt + 1}: Output validation failed. Retrying...")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: LLM call failed: {e}")
                if attempt == self.config.MAX_RETRIES:
                    # Fallback to original prompt if translation/expansion fails (and it's already Telugu)
                    # or return error/partial result.
                    if language == 'te':
                         return self._format_response(user_prompt, user_prompt, False, [])
                    else:
                        raise RuntimeError("Failed to generate valid Telugu prompt after retries.")

        # 4. Post-processing
        facets_integrated = extract_keywords(llm_output)
        expansion_applied = len(llm_output) > len(user_prompt) * 1.2 # Arbitrary threshold

        return self._format_response(user_prompt, llm_output.strip(), expansion_applied, facets_integrated)

    def _construct_system_prompt(self, user_prompt: str, language: str, facets: Dict[str, Any]) -> str:
        """
        Constructs the system prompt for the LLM.
        """
        genre = facets.get('genre', 'Not specified')
        keywords = ', '.join(facets.get('keywords', []) or ["None"])
        characters = ', '.join(facets.get('characters', []) or ["None"])
        locations = ', '.join(facets.get('locations', []) or ["None"])
        tone = facets.get('tone', 'Traditional')

        prompt = f"""
You are a Telugu story prompt optimizer for the Chandamama children's magazine archive.

USER INPUT: {user_prompt}
INPUT LANGUAGE: {language}
SELECTED FACETS:
- Genre: {genre}
- Keywords: {keywords}
- Characters: {characters}
- Locations: {locations}
- Tone: {tone}

YOUR TASKS:
1. TRANSLATE (if not Telugu) to natural, fluent Telugu.
2. EXPAND (if vague) with narrative elements.
3. PRESERVE INTENT (CRITICAL).
4. INTEGRATE FACETS naturally.

OUTPUT FORMAT:
Return ONLY the optimized Telugu prompt. No explanations.
"""
        return prompt

    def _validate_output(self, text: str) -> bool:
        """
        Validate that the output is predominantly Telugu.
        """
        if not text:
            return False
        total_chars = len(text)
        telugu_chars = count_telugu_chars(text)
        ratio = telugu_chars / total_chars if total_chars > 0 else 0
        return ratio >= self.config.MIN_TELUGU_RATIO

    def _format_response(self, original: str, optimized: str, expanded: bool, facets: List[str]) -> Dict[str, Any]:
        return {
            "original_prompt": original,
            "telugu_prompt": optimized,
            "expansion_applied": expanded,
            "facets_integrated": facets,
            "intent_preserved": True
        }

if __name__ == "__main__":
    # Simple test
    agent = PromptAgent()
    result = agent.process_prompt("clever farmer", "en", {"genre": "folk"})
    print(json.dumps(result, ensure_ascii=False, indent=2))
