from langgraph.graph import StateGraph, END
from src.agents.wf1_ingestion.ingestion_agent import IngestionAgent, IngestionState

# --- Nodes ---

def ingestion_node(state: IngestionState):
    agent = IngestionAgent()
    return agent.run(state)

# --- Graph Definition ---

workflow = StateGraph(IngestionState)

# Add Node
workflow.add_node("ingestion", ingestion_node)

# Set Entry Point
workflow.set_entry_point("ingestion")

# Add Edge to End
workflow.add_edge("ingestion", END)

# Compile
ingestion_app = workflow.compile()
