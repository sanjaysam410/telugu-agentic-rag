"""
Chandamama Agentic Engine - Ingestion UI Module
=================================================
Visualizes the 3-agent WF1 pipeline:
  Agent 1: Story Validation → Agent 2: Metadata Generation → Agent 3: Ingestion (MongoDB + Qdrant)
"""

import streamlit as st
import time
from datetime import datetime
from src.agents.wf1_ingestion.story_validation_agent import StoryValidationAgent, ValidationState
from src.agents.wf1_ingestion.metadata_agent import MetadataGenerationAgent, MetadataState
from src.agents.wf1_ingestion.ingestion_agent import IngestionAgent, IngestionState

# Genre Map for Translation
GENRE_MAP = {
    "Folklore": "జానపదం",
    "Mythology": "పురాణం",
    "Moral Story": "నీతి కథ",
    "Children's Story": "పిల్లల కథ",
    "Adventure": "సాహసం",
    "Comedy": "హాస్యం",
    "Mystery": "రహస్యం",
    "Poem": "గేయం",
    "Song": "పాట",
    "Other": "ఇతర"
}

def render_ingestion_ui():
    """Renders the simplified Consumer 'Contribute' UI."""

    # --- Custom CSS ---
    st.markdown("""
    <style>
        .stTextInput, .stTextArea { margin-bottom: 10px; }
        .success-box { padding: 1rem; background-color: #d4edda; color: #155724; border-radius: 0.5rem; }
        .error-box { padding: 1rem; background-color: #f8d7da; color: #721c24; border-radius: 0.5rem; }
    </style>
    """, unsafe_allow_html=True)

    # --- Title & Intro ---
    st.title("✍️ Contribute to Telugu Literature")
    st.markdown("Help us preserve and expand the world of Telugu stories. Submit your story below.")

    # --- Input Form ---
    with st.form("ingestion_form"):
        col1, col2 = st.columns([2, 1])

        with col1:
            story_text = st.text_area(
                "Story Text *",
                height=300,
                placeholder="Paste the full Telugu story here..."
            )

        with col2:
            title = st.text_input("Title *", placeholder="కథ పేరు")

            # Simple metadata
            genre_options = list(GENRE_MAP.keys())
            genre = st.selectbox("Genre", genre_options, index=2)

            author = st.text_input("Author (Optional)")

            # Grouped DOB/Date
            c1, c2 = st.columns(2)
            with c1:
                source_year = st.number_input("Year", min_value=1800, max_value=2025, value=None, placeholder="YYYY")
            with c2:
                source_month = st.number_input("Month", min_value=1, max_value=12, value=None, placeholder="MM")

            keywords_str = st.text_input("Keywords", placeholder="e.g. King, Forest, Magic")
            moral = st.text_input("Moral (Optional)")

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Submit Story", type="primary", use_container_width=True)

    # --- Process Submission ---
    if submitted:
        if not title or not title.strip():
            st.error("Please enter a Title.")
            return
        if not story_text or not story_text.strip():
            st.error("Please enter the Story Text.")
            return

        # User Fields
        user_fields = {
            "title": title,
            "language": "Telugu", # Defaulting as this is a Telugu portal
            "genre": GENRE_MAP.get(genre, genre),
            "contribution_timestamp": datetime.now().isoformat(),
        }
        if author: user_fields["author"] = author
        if moral: user_fields["moral"] = moral
        if keywords_str: user_fields["keywords"] = [k.strip() for k in keywords_str.split(",") if k.strip()]
        if source_year: user_fields["year"] = source_year
        if source_month: user_fields["month"] = source_month

        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # 1. Validation
            status_text.text("Validating content...")
            progress_bar.progress(20)

            validator = StoryValidationAgent()
            val_state = ValidationState(
                story_text=story_text,
                user_fields=user_fields,
                messages=[], errors=[]
            )
            val_result = validator.run(val_state)

            if val_result.validation_status != "success":
                progress_bar.empty()
                status_text.empty()
                st.error(f"Submission Rejected: {val_result.rejection_reason}")
                return

            # 2. Metadata (Hidden)
            status_text.text("Processing metadata...")
            progress_bar.progress(50)

            meta_agent = MetadataGenerationAgent()
            meta_state = MetadataState(
                text=story_text,
                source_type="story",
                user_fields=user_fields,
                messages=[], errors=[]
            )
            meta_result = meta_agent.run(meta_state)

            # 3. Ingestion
            status_text.text("Saving story...")
            progress_bar.progress(80)

            ingestion_metadata = {k: v for k, v in meta_result.extracted_metadata.items() if k != "full_text"}

            ingest_agent = IngestionAgent()
            ingest_state = IngestionState(
                story_text=story_text,
                metadata=ingestion_metadata,
                messages=[], errors=[]
            )
            ingest_result = ingest_agent.run(ingest_state)

            progress_bar.progress(100)
            status_text.empty()

            if ingest_result.status == "success":
                st.balloons()
                st.success("✅ Thank you! Your story has been successfully submitted.")
                with st.expander("View Submission Details"):
                    st.json(ingestion_metadata)
            else:
                st.error("Something went wrong during storage. Please try again.")

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
