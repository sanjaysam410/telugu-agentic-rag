"""
Chandamama Agentic Engine - Generation UI Module
===================================================
Visualizes the WF2 pipeline:
  Agent 1: Prompt Optimizer (Gemini) → Agent 2: Metadata Extraction (prompt mode)
  → Agent 3: RAG Agent (Vector Search + Story Generation) → Agent 4: Validator
"""

import streamlit as st
import time
import difflib
import re
from langchain_core.messages import HumanMessage

# --- Imports ---
from src.agents.wf2_generation.prompt_optimizer_agent import PromptOptimizerAgent, PromptState
from src.agents.wf1_ingestion.metadata_agent import MetadataGenerationAgent, MetadataState
from src.agents.wf2_generation.rag_agent import RAGAgent
from src.agents.wf2_generation.validator_agent import ValidatorAgent
from src.agents.base import AgentState

def render_generation_ui():
    """Renders the Consumer 'Story Generator' UI."""

    # --- Custom CSS ---
    st.markdown("""
    <style>
        .stTextArea textarea { font-size: 16px; }
        .story-container {
            padding: 2rem;
            background-color: #ffffff;
            color: #1e1e1e;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            font-family: 'Georgia', serif;
            line-height: 1.8;
        }
        .dark-mode .story-container {
            background-color: #2e2e2e;
            color: #d1d1d1;
        }
        div[data-testid="stExpander"] {
            border: 1px solid #444;
            border-radius: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- Sidebar: Advanced Options ---
    with st.sidebar:
        st.header("Advanced Options")
        length = st.select_slider("Length (approx)", options=["Short", "Medium", "Long"], value="Medium")
        characters_str = st.text_input("Characters", placeholder="Raju, Rani")
        locations_str = st.text_input("Locations", placeholder="Forest, Kingdom")

    # --- Main Interface ---
    st.title("✨ Telugu Story Generator")
    st.caption("Create unique Telugu stories with AI. Customize settings and describe your idea.")

    # --- Story Settings (Main Area) ---
    with st.container(border=True):
        st.markdown("##### 🛠️ Story Settings")
        c1, c2, c3 = st.columns(3)

        with c1:
            genre_map = {
                "Folklore (జానపదం)": "Folklore",
                "Mythology (పురాణం)": "Mythology",
                "Moral Story (నీతి కథ)": "Moral Story",
                "Children's (పిల్లల కథ)": "Children's Story",
                "Adventure (సాహసం)": "Adventure",
                "Comedy (హాస్యం)": "Comedy",
                "Mystery (రహస్యం)": "Mystery",
                "Poem (గేయం)": "Poem",
            }
            genre_label = st.selectbox("Genre", list(genre_map.keys()), index=2)
            genre = genre_map[genre_label]

        with c2:
            tone = st.selectbox("Tone", ["Traditional", "Modern", "Humorous", "Dramatic", "Poetic", "Simple"], index=0)

        with c3:
            target_age = st.selectbox("Audience", ["Children (3-8)", "Pre-Teens (9-12)", "Teens (13+)", "General"], index=1)

    # --- Prompt Area ---
    with st.form("generation_form"):
        st.markdown("##### 📝 Description")
        user_prompt = st.text_area(
            "Prompt",
            height=120,
            placeholder="e.g. A clever rabbit outsmarts a lion in the deep forest...",
            label_visibility="collapsed"
        )

        submitted = st.form_submit_button("Generate Story ✨", type="primary", use_container_width=True)

    # --- Generation Layout ---
    if submitted:
        if not user_prompt or not user_prompt.strip():
            st.warning("Please describe a story idea first.")
            return

        # Prepare Inputs
        user_facets = {"genre": genre, "tone": tone, "target_age": target_age, "length": length}
        if characters_str: user_facets["characters"] = [c.strip() for c in characters_str.split(",") if c.strip()]
        if locations_str: user_facets["locations"] = [l.strip() for l in locations_str.split(",") if l.strip()]

        try:
            # --- Creative Loading Animation ---
            loading_ph = st.empty()
            loading_messages = [
                "✨ Weaving your story...",
                "🦁 Summoning characters...",
                "📜 Consulting ancient scrolls...",
                "🎭 Setting the stage...",
                "💎 Polishing the gems..."
            ]

            # Helper to update loading message
            def update_loading(idx):
                msg = loading_messages[idx % len(loading_messages)]
                loading_ph.markdown(f"<div style='text-align:center; font-size:1.2em; color:#666;'>{msg}</div>", unsafe_allow_html=True)

            # 1. Prompt Optimization
            update_loading(0)
            optimizer = PromptOptimizerAgent()
            has_telugu = any('\u0C00' <= c <= '\u0C7F' for c in user_prompt)
            prompt_state = PromptState(
                user_prompt=user_prompt,
                input_language="te" if has_telugu else "en",
                user_facets=user_facets,
                messages=[], errors=[]
            )
            prompt_result = optimizer.run(prompt_state)

            # 2. Metadata
            update_loading(1)
            meta_agent = MetadataGenerationAgent()
            meta_state = MetadataState(
                text=prompt_result.optimized_prompt,
                source_type="prompt",
                user_fields={"language": "Telugu", "genre": genre},
                messages=[], errors=[]
            )
            meta_result = meta_agent.run(meta_state)
            rag_keywords = meta_result.extracted_metadata.get("keywords", [])

            # 3. RAG + Generation
            update_loading(2)
            rag_agent = RAGAgent()
            rag_metadata = {"keywords": rag_keywords, "genre": genre}
            rag_state = AgentState(
                messages=[HumanMessage(content=prompt_result.optimized_prompt)],
                metadata={
                    "telugu_prompt": prompt_result.optimized_prompt,
                    "metadata": rag_metadata,
                    "user_facets": user_facets,
                },
                errors=[]
            )
            rag_result = rag_agent.run(rag_state)
            generated_story = rag_result.metadata.get("generated_story", "")

            # 4. Validation
            update_loading(4) # Skip to Polishing
            validator = ValidatorAgent()
            val_state = AgentState(
                messages=rag_result.messages,
                metadata=rag_result.metadata,
                errors=[]
            )
            val_result = validator.run(val_state)
            final_story = val_result.metadata.get("generated_story", generated_story)

            # Clear loading
            loading_ph.empty()

            # --- Result Display (Streaming Effect) ---
            if final_story:
                st.markdown("### 📖 Your Story")

                # 1. Parse Title (if present) BEFORE creating story box
                display_story = final_story
                # Regex handles: Title:, **Title:**, # Title:, Title -, etc.
                title_match = re.search(r"(?:^|\n)(?:\*\*|#\s*)?(?:Title|శీర్షిక)(?:\*\*|:)?\s*[:\-]\s*(.*?)(?:\n|$)", final_story, re.IGNORECASE)

                if title_match:
                    raw_title = title_match.group(1).strip()
                    # Clean up bold markers from the title itself
                    clean_title = raw_title.replace("**", "").replace("*", "").strip()
                    st.subheader(f"📑 {clean_title}")

                    # Remove the Title line from the body for cleaner display
                    start, end = title_match.span()
                    display_story = (final_story[:start] + final_story[end:]).strip()

                    # Also clean up "Story:" label if it appears right after
                    display_story = re.sub(r"^(?:\*\*|#\s*)?(?:Story|కథ)(?:\*\*|:)?\s*[:\-]\s*", "", display_story, flags=re.IGNORECASE).strip()

                # Container for story body
                story_box = st.empty()
                streamed_text = ""

                # 2. Helper for Markdown -> HTML (Bold/Italic)
                def md_to_html(text):
                    # Bold **text** -> <b>text</b>
                    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                    # Bold __text__ -> <b>\1</b>
                    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
                    # Italic *text* -> <i>\1</i>
                    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
                    # Newlines -> <br>
                    text = text.replace("\n", "<br>")
                    return text

                # 3. Typewriter effect
                # Split by spaces to stream words
                # We use display_story (body) for streaming
                words = display_story.split(" ")

                for word in words:
                    streamed_text += word + " "

                    # Convert accumulated text to HTML for display
                    clean_html = md_to_html(streamed_text)

                    story_box.markdown(f'<div class="story-container">{clean_html}</div>', unsafe_allow_html=True)
                    time.sleep(0.03) # Adjust speed here

                # Final render to ensure perfect formatting
                final_html = md_to_html(display_story)
                story_box.markdown(f'<div class="story-container">{final_html}</div>', unsafe_allow_html=True)

                # Download Button (Full text including Title)
                st.download_button("Download Text", final_story, file_name="story.txt")

            else:
                st.error("Sorry, I couldn't generate a story this time. Please try again.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
