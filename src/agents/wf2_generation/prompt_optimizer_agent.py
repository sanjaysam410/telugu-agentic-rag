"""
WF2 Agent 1: Prompt Optimizer Agent.
Ported from telugu-agents/agents/prompt_agent.py
Uses Gemini (Language LLM) to translate/optimize prompts into rich Telugu.
"""

import re
import json
from typing import Dict, Any, List
from src.agents.base import BaseAgent, AgentState
from src.config import Config
from langchain_core.messages import SystemMessage, HumanMessage

# --- State Definition ---
class PromptState(AgentState):
    """
    State for the Prompt Optimizer.
    Input: user_prompt, input_language, user_facets
    Output: optimized_prompt, telugu_prompt, extracted_keywords, expansion_applied
    """
    user_prompt: str = ""
    input_language: str = "en"  # te, en, hi, ta, kn, ml
    user_facets: Dict[str, Any] = {}
    optimized_prompt: str = ""
    telugu_prompt: str = ""
    extracted_keywords: List[str] = []
    expansion_applied: bool = False
    status: str = "pending"


# Telugu validation helpers (ported from telugu-agents/utils/telugu_utils.py)
def _count_telugu_chars(text: str) -> int:
    return len([c for c in text if '\u0C00' <= c <= '\u0C7F'])

def _extract_keywords_from_text(text: str) -> List[str]:
    """Extract Telugu keywords from text (heuristic)."""
    words = text.split()
    telugu_pattern = re.compile(r'[\u0C00-\u0C7F]')
    keywords = [w.strip('.,!?') for w in words if telugu_pattern.search(w) and len(w) > 2]
    return list(set(keywords))


class PromptOptimizerAgent(BaseAgent):
    """
    WF2 Agent 1: Prompt Optimizer.
    Ported from telugu-agents/agents/prompt_agent.py.

    Takes user prompt (any language) → Uses Gemini to:
      1. TRANSLATE (if not Telugu) to natural, fluent Telugu.
      2. EXPAND (if vague) with narrative elements.
      3. PRESERVE INTENT.
      4. INTEGRATE FACETS naturally.
    → Outputs optimized Telugu prompt + auto-extracted keywords.
    """

    MAX_RETRIES = 2
    MIN_TELUGU_RATIO = 0.5

    def __init__(self):
        super().__init__(name="PromptOptimizerAgent")

    def run(self, state: PromptState) -> PromptState:
        self.log_step("Start", f"Optimizing prompt: '{state.user_prompt[:80]}...' (lang: {state.input_language})")

        user_prompt = state.user_prompt
        if not user_prompt or not user_prompt.strip():
            state.status = "failure"
            state.errors.append("Empty prompt provided")
            return state

        # Construct the LLM prompt (mirroring telugu-agents/prompt_agent.py)
        llm_prompt = self._construct_system_prompt(
            user_prompt, state.input_language, state.user_facets
        )

        # Call LLM with retries + Telugu validation
        llm_output = ""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                self.log_step("Gemini", f"Calling Language Model (attempt {attempt + 1})...")
                llm_output = self._call_gemini(llm_prompt)

                if self._validate_telugu_output(llm_output):
                    self.log_step("Validation", "Output passed Telugu ratio check ✓")
                    break
                else:
                    self.logger.warning(f"Attempt {attempt + 1}: Telugu ratio too low. Retrying...")
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1}: LLM call failed: {e}")
                if attempt == self.MAX_RETRIES:
                    # Fallback: if input is Telugu, use it directly
                    if state.input_language == "te":
                        llm_output = user_prompt
                        self.log_step("Fallback", "Using original Telugu prompt as-is")
                    else:
                        state.status = "failure"
                        state.errors.append(f"Prompt optimization failed after {self.MAX_RETRIES + 1} attempts: {str(e)}")
                        return state

        # Post-processing
        optimized = llm_output.strip()
        keywords = _extract_keywords_from_text(optimized)
        expansion_applied = len(optimized) > len(user_prompt) * 1.2

        state.optimized_prompt = optimized
        state.telugu_prompt = optimized
        state.extracted_keywords = keywords
        state.expansion_applied = expansion_applied
        state.status = "success"

        self.log_step("Success", f"Optimized prompt: {len(optimized)} chars, {len(keywords)} keywords extracted")
        return state

    def _construct_system_prompt(self, user_prompt: str, language: str, facets: Dict[str, Any]) -> str:
        """
        Constructs the LLM prompt. Mirrors telugu-agents/agents/prompt_agent.py._construct_system_prompt
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

    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini via our Language LLM (LangChain)."""
        llm = self.language_llm  # Gemini via BaseAgent
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        return response.content

    def _validate_telugu_output(self, text: str) -> bool:
        """Validate that the output is predominantly Telugu."""
        if not text:
            return False
        total_chars = len(text)
        telugu_chars = _count_telugu_chars(text)
        ratio = telugu_chars / total_chars if total_chars > 0 else 0
        return ratio >= self.MIN_TELUGU_RATIO
