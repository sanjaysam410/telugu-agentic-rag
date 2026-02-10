from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel
from langchain_core.messages import BaseMessage
from src.config import get_reasoning_llm, get_language_llm, Config

# Setup logger for agents
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class AgentState(BaseModel):
    """Base state for all agents."""
    messages: list[BaseMessage] = []
    metadata: Dict[str, Any] = {}
    errors: list[str] = []

class BaseAgent(ABC):
    """
    Abstract Base Class for all agents in the Telugu Agentic RAG system.
    Provides standard access to Hybrid Models (Reasoning vs Language).
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
        self.config = Config()

        # Lazy loading of LLMs to avoid initialization cost if not needed
        self._reasoning_llm = None
        self._language_llm = None

    @property
    def reasoning_llm(self):
        """Access the Reasoning Engine (GPT-OSS)."""
        if not self._reasoning_llm:
            self.logger.info("Initializing Reasoning LLM (GPT-OSS)...")
            self._reasoning_llm = get_reasoning_llm()
        return self._reasoning_llm

    @property
    def language_llm(self):
        """Access the Language Engine (Gemini)."""
        if not self._language_llm:
            self.logger.info("Initializing Language LLM (Gemini)...")
            self._language_llm = get_language_llm()
        return self._language_llm

    @abstractmethod
    def run(self, state: AgentState) -> AgentState:
        """
        Main execution logic for the agent.
        Must be implemented by subclasses.
        """
        pass

    def log_step(self, step_name: str, details: str = ""):
        """Standardized logging for agent steps."""
        self.logger.info(f"[{self.name}] Step: {step_name} | {details}")

    def handle_error(self, error: Exception, state: AgentState) -> AgentState:
        """Standard error handling."""
        error_msg = f"{self.name} Error: {str(error)}"
        self.logger.error(error_msg, exc_info=True)
        state.errors.append(error_msg)
        return state
