"""
Chandamama Agentic Engine - Ingestion Workflow UI (Standalone)
==============================================================
"""

import streamlit as st
from dotenv import load_dotenv

# Load env before imports
load_dotenv()

from src.ui.ingestion_ui import render_ingestion_ui

# --- Page Config ---
st.set_page_config(
    page_title="Chandamama Ingestion Pipeline",
    page_icon="🐘",
    layout="wide"
)

if __name__ == "__main__":
    render_ingestion_ui()
