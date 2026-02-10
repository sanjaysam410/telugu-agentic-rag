
import streamlit as st
import json
import os
import sys

from agents.prompt_agent import PromptAgent

# Page config
st.set_page_config(
    page_title="Telugu Prompt Optimizer",
    page_icon="✍️",
    layout="wide"
)

# Title and description
st.title("✍️ Telugu RAG Prompt Optimizer")
st.markdown("Transform your story ideas into rich, optimized Telugu prompts for the RAG system.")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    language = st.selectbox("Input Language", ["English", "Telugu", "Hindi", "Tamil", "Kannada", "Malayalam"])

    st.subheader("Facets")
    genre = st.text_input("Genre", placeholder="e.g. Folk, Adventure, Moral")
    tone = st.selectbox("Tone", ["Traditional", "Modern", "Mythological", "Humorous", "Serious"])

    keywords_input = st.text_area("Keywords (comma separated)", placeholder="e.g. king, forest, magic")
    characters_input = st.text_area("Characters (comma separated)", placeholder="e.g. old woman, clever thief")
    locations_input = st.text_area("Locations (comma separated)", placeholder="e.g. village, palace, river bank")

# Main content area
col1, col2 = st.columns(2)

with col1:
    st.subheader("Input")
    user_prompt = st.text_area("Enter your story idea:", height=200, placeholder="Type your story prompt here...")

    generate_btn = st.button("✨ Optimize Prompt", type="primary")

with col2:
    st.subheader("Result")
    result_container = st.container()

# Logic
if generate_btn:
    if not user_prompt:
        st.error("Please enter a story prompt.")
    else:
        with st.spinner("Optimizing your prompt for Telugu storytelling..."):
            try:
                # Prepare facets
                facets = {
                    "genre": genre if genre else None,
                    "tone": tone,
                    "keywords": [k.strip() for k in keywords_input.split(',')] if keywords_input else [],
                    "characters": [c.strip() for c in characters_input.split(',')] if characters_input else [],
                    "locations": [l.strip() for l in locations_input.split(',')] if locations_input else []
                }

                # Default language code mapping (simple heuristic for demo)
                lang_map = {
                    "English": "en", "Telugu": "te", "Hindi": "hi",
                    "Tamil": "ta", "Kannada": "kn", "Malayalam": "ml"
                }
                lang_code = lang_map.get(language, "en")

                # Initialize agent
                # Note: Ideally API key is from env, assuming it's set or hardcoded/fallback in agent for now
                agent = PromptAgent()

                # Process
                result = agent.process_prompt(user_prompt, lang_code, facets)

                # Display Result
                with result_container:
                    if result.get("telugu_prompt"):
                        st.success("Optimization Complete!")
                        st.markdown("### 📜 Telugu Prompt")
                        st.info(result["telugu_prompt"])

                        with st.expander("See Full JSON Output"):
                            st.json(result)

                        st.markdown(f"**Expansion Applied:** `{result.get('expansion_applied')}`")
                        st.markdown(f"**Facets Integrated:** {', '.join(result.get('facets_integrated', []))}")
                    else:
                        st.error("Failed to generate prompt.")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
