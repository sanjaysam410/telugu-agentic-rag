from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from agentic_engine import config

class BaseAgent(ABC):
    """
    Base class for all agents in the Agentic Engine.
    Standardizes input/output formats and logging.
    """

    def __init__(self, agent_name: str, config: Optional[Dict[str, Any]] = None):
        self.agent_name = agent_name
        self.config = config or {}

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for the agent.
        Must return a dict with "status", "payload", "metadata", or "error".
        """
        pass

    def success(self, payload: Dict[str, Any], meta: Dict[str, Any] = None) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_name,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "payload": payload,
            "metadata": meta or {}
        }

    def failure(self, error_code: str, message: str, meta: Dict[str, Any] = None) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_name,
            "status": "failure",
            "timestamp": datetime.now().isoformat(),
            "error": {
                "code": error_code,
                "message": message
            },
            "metadata": meta or {}
        }

    def pass_through(self, input_data: Dict[str, Any], reason: str) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_name,
            "status": "skipped",
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "payload": input_data
        }
