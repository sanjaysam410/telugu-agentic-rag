from langgraph.graph import StateGraph, END
from src.agents.wf2_generation.rag_agent import RagAgent, RagState
from src.agents.wf2_generation.validator_agent import ValidatorAgent, ValidationState

# --- Node Wrappers ---

def rag_node(state: dict):
    agent = RagAgent()
    # If feedback exists from Validator, append to prompt or context
    prompt = state.get("user_prompt", "")
    feedback = state.get("critique_feedback", [])

    if feedback and state.get("status") == "rejected":
        # Augment prompt with feedback for regeneration
        feedback_str = "; ".join(feedback)
        prompt = f"{prompt}\n\n[Previous Feedback]: The last draft was rejected because: {feedback_str}. Please improve."

    rag_state = RagState(user_prompt=prompt)
    rag_state.retrieved_docs = state.get("retrieved_docs", []) # Reuse retrieved docs if available

    result = agent.run(rag_state)

    # Return updated state
    return {
        "user_prompt": state.get("user_prompt"), # Keep original prompt key
        "story_draft": result.story_draft,
        "retrieved_docs": result.retrieved_docs,
        "status": "generated"
    }

def validator_node(state: dict):
    agent = ValidatorAgent()
    result = agent.run(ValidationState(
        story_draft=state.get("story_draft", ""),
        user_prompt=state.get("user_prompt", "")
    ))
    return {
        "user_prompt": state.get("user_prompt"),
        "story_draft": state.get("story_draft"), # Keep draft
        "retrieved_docs": state.get("retrieved_docs"),
        "validation_score": result.score,
        "critique_feedback": result.feedback,
        "story_final": result.final_story,
        "status": result.status
    }

# --- Conditional Logic ---

def should_loop(state: dict):
    """Check if we need to regenerate."""
    # Safety Check: Stop after 3 attempts to prevent infinite loops (cost control)
    attempts = state.get("attempts", 0)

    # If we hit the limit, we FORCE end, regardless of rejection status
    if attempts >= 3:
        return "end"

    status = state.get("status")
    if status == "rejected":
        # Increment attempt counter
        state["attempts"] = attempts + 1
        return "regenerate"

    return "end"

# --- Graph Definition ---

workflow = StateGraph(dict) # Using dict state for flexible passing

# Add Nodes
workflow.add_node("rag", rag_node)
workflow.add_node("validator", validator_node)

# Set Entry Point
workflow.set_entry_point("rag")

# Edges
workflow.add_edge("rag", "validator")

# Conditional Edge
workflow.add_conditional_edges(
    "validator",
    should_loop,
    {
        "regenerate": "rag",
        "end": END
    }
)

# Compile
generation_app = workflow.compile()
