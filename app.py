"""
Chandamama Agentic Engine - Unified App
=======================================
Combines Ingestion and Generation workflows into a single interface.
"""

import streamlit as st
from dotenv import load_dotenv
import logging

# Load env before imports
load_dotenv()

# --- Page Config (Must be first Streamlit command) ---
st.set_page_config(
    page_title="Chandamama Agentic Engine",
    page_icon="🐘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Imports ---
from src.ui.ingestion_ui import render_ingestion_ui
from src.ui.generation_ui import render_generation_ui
from src.ui.settings_ui import render_settings_ui
from src.config import Config

# --- Session State Init ---
if "llm_settings" not in st.session_state:
    st.session_state["llm_settings"] = {
        "model": "openai/gpt-oss-120b",
        "temperature": 0.7
    }

# --- Runtime Config Patch ---
# Force GPT-OSS 120B as requested for consumer mode
if Config.REASONING_MODEL_NAME != "openai/gpt-oss-120b":
    Config.REASONING_MODEL_NAME = "openai/gpt-oss-120b"

# --- Sidebar Navigation ---
st.sidebar.title("📚 Telugu Stories")
st.sidebar.caption("Preserving Culture with AI")

app_mode = st.sidebar.radio(
    "Menu",
    ["Story Generator", "Contribute", "Settings"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info("Powered by **GPT-OSS 120B**")

# --- Routing ---
if app_mode == "Contribute":
    render_ingestion_ui()
elif app_mode == "Story Generator":
    render_generation_ui()
elif app_mode == "Settings":
    render_settings_ui()
