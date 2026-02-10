from typing import Any, Dict, List
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.agents.base import BaseAgent, AgentState
from src.config import Config

class ValidatorAgent(BaseAgent):
    """
    Agent 4: Validator Agent
    Critiques the generated story, auto-corrects minor issues, and flags major issues.
    """

    def __init__(self):
        super().__init__(name="ValidatorAgent")
        # Ensure language LLM is loaded
        _ = self.language_llm

    def run(self, state: AgentState) -> AgentState:
        """
        Executes Validation Flow:
        1. Extract generated story.
        2. Analyze using Gemini.
        3. Parse result (Accept/Reject/Fixed).
        4. Update state.
        """
        self.logger.info("Validator Agent started.")

        # 1. Extract Input
        story = state.metadata.get("generated_story", "")
        if not story:
            # Fallback: check last message
            if state.messages and state.messages[-1].type == "ai":
                story = state.messages[-1].content
            else:
                 error_msg = "No generated story found to validate."
                 self.logger.error(error_msg)
                 return self.handle_error(ValueError(error_msg), state)

        # 2. Construct Prompt
        # We ask for JSON output for easier parsing
        system_prompt = """You are a Senior Telugu Language Editor (Pundit) for Chandamama.
Your task is to REVIEW and EDIT a given Telugu story.

*** CRITICAL INSTRUCTION: DO NOT KILL THE CREATIVITY ***
- Your goal is to POLISH, not REWRITE.
- Respect the author's unique voice and stylistic choices.
- Only intervene for OBJECTIVE errors and violations of the 8-Point Quality Standard.

THE 8-POINT QUALITY CHECKLIST:
1. **Show, Don't Tell**: If the first paragraph dumps traits (e.g., "Raju is a greedy man"), REWRITE IT to show action.
2. **No Double Morals**: If the story narrative PREACHES the moral *and* there is a 'Moral:' section at the end, DELETE the preaching from the story body.
3. **Pacing**: If the ending feels rushed or uses "magically", flag calls for a fix or rejection.
4. **Logic**: Ensure strict cause-and-effect.

DECISION LOGIC:
- **MINOR ISSUES** (Spelling, Grammar, 'Telling' Intros, Preachiness, Gender slip):
  -> ACTION: **FIX** them directly in 'fixed_story'.
  -> STATUS: "FIXED"
  -> NOTE: **STRICTLY PRESERVE "Title: <Text>" format at the start.**

- **MAJOR ISSUES** (Rushed Ending, Broken Logic, Incoherent):
  -> ACTION: Explain why in critique.
  -> STATUS: "REJECT"

- **NO ISSUES**:
  -> ACTION: Keep as is.
  -> STATUS: "ACCEPT"

OUTPUT FORMAT (JSON ONLY):
{
  "score": (Integer 0-10, deduct points for 'Telling' and 'Preaching'),
  "status": "ACCEPT" | "FIXED" | "REJECT",
  "fixed_story": "Full text of the story (only if FIXED or ACCEPT, else empty string)",
  "critique": ["List of specific issues found..."]
}
"""

        user_prompt = f"Here is the story to review:\n\n{story}"

        # 3. Call LLM
        self.log_step("Validation", "Analyzing story...")
        try:
            # We use the Language Model (Gemini) for this task details
            response = self.language_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            # 4. Parse Output
            content = response.content
            # Clean up markdown code blocks if present
            if "```json" in content:
                content = content.replace("```json", "").replace("```", "")
            elif "```" in content:
                content = content.replace("```", "")

            result = json.loads(content.strip())

            score = result.get("score", 0)
            status = result.get("status", "REJECT")
            fixed_story = result.get("fixed_story", "")
            critique = result.get("critique", [])

            self.log_step("Validation", f"Result: {status} (Score: {score})")

            # 5. Update State
            state.metadata["validation_score"] = score
            state.metadata["validation_status"] = status
            state.metadata["critique_feedback"] = critique

            if status == "FIXED" and fixed_story:
                self.logger.info("Applying validator fixes to the story.")
                # Update the last AI message with the fixed version
                state.messages[-1] = AIMessage(content=fixed_story)
                state.metadata["generated_story"] = fixed_story
                state.metadata["is_polished"] = True

            elif status == "ACCEPT":
                 state.metadata["is_polished"] = True

            # If REJECT, we just store the feedback. The graph controller would decide what to do (e.g., loop back).

        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            state.errors.append(f"Validation Error: {str(e)}")
            # Fallback: Assume accept if validation fails technically, but log error
            state.metadata["validation_status"] = "ERROR"

        return state
