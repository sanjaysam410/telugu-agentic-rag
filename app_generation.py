"""
Chandamama Agentic Engine - Generation Workflow UI (Standalone)
===============================================================
"""

import streamlit as st
from dotenv import load_dotenv

# Load env before imports
load_dotenv()

from src.ui.generation_ui import render_generation_ui

# --- Page Config ---
st.set_page_config(
    page_title="Chandamama Story Generator",
    page_icon="📖",
    layout="wide"
)

if __name__ == "__main__":
    if "user_prompt_val" not in st.session_state:
        st.session_state["user_prompt_val"] = ""
    render_generation_ui()
