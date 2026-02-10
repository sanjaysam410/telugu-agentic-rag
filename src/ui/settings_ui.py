"""
Chandamama Agentic Engine - Settings UI Module
==============================================
"""

import streamlit as st
from src.config import Config

def render_settings_ui():
    """Renders the Consumer Settings UI."""
    st.header("⚙️ Settings")
    st.divider()

    st.subheader("🤖 AI Model")
    st.info("**Current Model:** OpenAI GPT-OSS 120B")
    st.caption("This model is optimized for high-quality Telugu storytelling.")

    # Enforce the model in Config just in case
    if Config.REASONING_MODEL_NAME != "openai/gpt-oss-120b":
        Config.REASONING_MODEL_NAME = "openai/gpt-oss-120b"

    st.divider()

    st.subheader("🎨 Creativity")
    current_temp = st.session_state.get("llm_settings", {}).get("temperature", 0.7)
    temp = st.slider("Creativity Level", 0.0, 1.0, current_temp, 0.1, help="Lower = Predicable, Higher = Creative")

    if "llm_settings" not in st.session_state:
        st.session_state["llm_settings"] = {}
    st.session_state["llm_settings"]["temperature"] = temp

    st.caption(f"Current Value: {temp}")
