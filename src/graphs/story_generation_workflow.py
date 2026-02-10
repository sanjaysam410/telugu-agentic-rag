from typing import Dict, Any, TypedDict, List
from langgraph.graph import StateGraph, END

from src.agents.base import AgentState
from src.agents.wf2_generation.rag_agent import RAGAgent
from src.agents.wf2_generation.validator_agent import ValidatorAgent
import logging

# Setup logger
logger = logging.getLogger("graph.story_generation")

# Define Graph State (inherits from AgentState but compatible with LangGraph)
class GraphState(TypedDict):
    messages: List[Any]
    metadata: Dict[str, Any]
    errors: List[str]
    attempts: int
    history: List[Dict[str, Any]] # Added history tracking

# Initialize Agents
rag_agent = RAGAgent()
validator_agent = ValidatorAgent()

def generate_story_node(state: GraphState):
    """Executes RAG Agent to generate story."""
    logger.info(f"Node: Generating Story (Attempt {state.get('attempts', 0) + 1})")

    # Convert GraphState to AgentState for the agent
    agent_state = AgentState(
        messages=state["messages"],
        metadata=state["metadata"],
        errors=state.get("errors", [])
    )

    # Run Agent
    result = rag_agent.run(agent_state)

    # Update GraphState
    return {
        "messages": result.messages,
        "metadata": result.metadata,
        "errors": result.errors,
        "attempts": state.get("attempts", 0) + 1,
        "history": state.get("history", []) # Pass through history
    }

def validate_story_node(state: GraphState):
    """Executes Validator Agent and updates history."""
    logger.info("Node: Validating Story")

    agent_state = AgentState(
        messages=state["messages"],
        metadata=state["metadata"],
        errors=state.get("errors", [])
    )

    result = validator_agent.run(agent_state)

    # Capture snapshot for history
    snapshot = {
        "attempt": state.get("attempts", 1),
        "story": result.metadata.get("generated_story", ""),
        "score": result.metadata.get("validation_score", 0),
        "status": result.metadata.get("validation_status", "UNKNOWN"),
        "critique": result.metadata.get("critique_feedback", [])
    }

    current_history = state.get("history", [])
    new_history = current_history + [snapshot]

    return {
        "messages": result.messages,
        "metadata": result.metadata,
        "errors": result.errors,
        "history": new_history
    }

def router(state: GraphState):
    """Decides next step based on Validation Status."""
    status = state["metadata"].get("validation_status", "REJECT")
    attempts = state.get("attempts", 0)
    scores = state["metadata"].get("validation_score", 0)

    logger.info(f"Router: Status={status}, Attempts={attempts}, Score={scores}")

    if status == "ACCEPT" or status == "FIXED":
        return "end"

    if status == "REJECT":
        # Infinite loop with safety break (e.g. 10) to prevent runaway costs
        if attempts >= 10:
            logger.warning("Max attempts reached. Stopping loop despite rejection.")
            return "end"
        else:
            return "retry"

    return "end"

# Build Graph
workflow = StateGraph(GraphState)

workflow.add_node("generate_story", generate_story_node)
workflow.add_node("validate_story", validate_story_node)

workflow.set_entry_point("generate_story")

workflow.add_edge("generate_story", "validate_story")

workflow.add_conditional_edges(
    "validate_story",
    router,
    {
        "retry": "generate_story",
        "end": END
    }
)

# Compile
story_generation_app = workflow.compile()
