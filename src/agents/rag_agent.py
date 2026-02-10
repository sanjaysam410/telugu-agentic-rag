from typing import Dict, Any, List
from langchain_core.messages import AIMessage

from src.agents.base import BaseAgent, AgentState
from src.retrieval.vector_search import StoryEmbeddingsRetriever
from src.utils.generation_utils import generate_story
from src.config import Config

class RAGAgent(BaseAgent):
    """
    Agent 3: RAG Agent
    Retrieves relevant context and generates a new story based on the optimized prompt.
    """

    def __init__(self):
        super().__init__(name="RAGAgent")
        # Initialize retriever
        try:
            self.retriever = StoryEmbeddingsRetriever(top_k=Config.TOP_K_RETRIEVAL)
            self.logger.info("RAG Agent initialized with StoryEmbeddingsRetriever.")
        except Exception as e:
            self.logger.error(f"Failed to initialize retriever: {e}")
            self.retriever = None

    def run(self, state: AgentState) -> AgentState:
        """
        Executes the RAG flow:
        1. Retrieve context based on prompt + keywords.
        2. Generate story using LLM + Context.
        """
        self.logger.info("RAG Agent started.")

        # Extract inputs from state
        # We expect a structured input or the last message to contain the prompt details
        # For this implementation, we look for 'telugu_prompt' and 'metadata' in state.metadata
        # If not present, we fall back to the last user message.

        telugu_prompt = state.metadata.get("telugu_prompt")
        metadata = state.metadata.get("metadata", {})
        user_facets = state.metadata.get("user_facets", {})

        if not telugu_prompt:
            # Fallback: Check if last message is from user (simplistic fallback)
             if state.messages and state.messages[-1].type == "human":
                 telugu_prompt = state.messages[-1].content
             else:
                 error_msg = "No telugu_prompt found in state metadata or messages."
                 return self.handle_error(ValueError(error_msg), state)

        # 1. RETRIEVAL
        self.log_step("Retrieval", f"Querying for: {telugu_prompt[:50]}...")

        context_text = ""
        try:
            if self.retriever:
                # Enrich query with keywords if available
                keywords = metadata.get("keywords", [])
                keyword_str = " ".join(keywords) if keywords else ""
                search_query = f"{telugu_prompt} {keyword_str}".strip()

                context_text = self.retriever.retrieve(search_query)
                self.log_step("Retrieval", "Context retrieved successfully.")
            else:
                 self.logger.warning("Retriever not initialized. Skipping retrieval.")
        except Exception as e:
            self.logger.error(f"Retrieval failed: {e}")
            # We proceed without context if retrieval fails, but log it.
            state.errors.append(f"Retrieval warning: {str(e)}")

        # 2. GENERATION
        self.log_step("Generation", "Starting story generation...")

        # Prepare facets for generation utility
        # Merge user_facets with extracted metadata

        prompt_input = telugu_prompt

        # Check for critique from Validator (Feedback Loop)
        critique = state.metadata.get("critique_feedback", [])
        if critique and len(critique) > 0:
             critique_text = "\n".join(critique)
             self.logger.info(f"Applying critique to generation: {critique_text}")
             prompt_input += f"\n\n[IMPORTANT: The previous version was rejected. Please FIX the following issues:\n{critique_text}\n]"

        generation_facets = {
            "prompt_input": prompt_input,
            "genre": user_facets.get("genre", metadata.get("genre", "Folklore")),
            "keywords": metadata.get("keywords", []),
            "characters": user_facets.get("characters", metadata.get("characters_inferred", [])),
            "locations": user_facets.get("locations", metadata.get("locations_inferred", [])),
            "tone": user_facets.get("tone", "traditional")
        }

        try:
            # generate_story returns a generator. We consume it to get the full text.
            # In a real async app, we might stream this to the user.
            # Here, the agent completes the work and returns the full story.
            story_generator = generate_story(generation_facets, context_text)

            full_story = ""
            for chunk in story_generator:
                full_story += chunk

            self.log_step("Generation", f"Story generated. Length: {len(full_story)} chars.")

            # Store result
            # We append an AIMessage with the story
            state.messages.append(AIMessage(content=full_story))

            # Update metadata
            state.metadata["generated_story"] = full_story
            state.metadata["retrieved_context"] = context_text

        except Exception as e:
            return self.handle_error(e, state)

        self.logger.info("RAG Agent finished successfully.")
        return state
