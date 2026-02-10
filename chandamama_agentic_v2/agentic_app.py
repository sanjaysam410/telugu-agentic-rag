import streamlit as st
import json
from datetime import datetime
from unittest.mock import patch
from agentic_engine.agents.story_validation_agent import StoryValidationAgent
from agentic_engine.agents.metadata_generation_agent import MetadataGenerationAgent

# Page Config
st.set_page_config(
    page_title="Chandamama Agentic Engine",
    page_icon="🐘",
    layout="wide"
)

# Sidebar Configuration
st.sidebar.title("Agent Control Panel")
mock_llm = st.sidebar.checkbox("Mock LLM Responses", value=False, help="Use mock responses to save costs/time or if API keys are missing.")

# Utilities: Genre Translation Map
GENRE_MAP = {
    "Folklore": {"Telugu": "జానపదం", "Hindi": "లోకకథ", "English": "Folklore"},
    "Mythology": {"Telugu": "పురాణం", "Hindi": "పౌరాణిక", "English": "Mythology"},
    "Moral Story": {"Telugu": "నీతి కథ", "Hindi": "నీతి కథ", "English": "Moral Story"},
    "Nursery Rhyme": {"Telugu": "బాలగేయం", "Hindi": "బాలగేయం", "English": "Nursery Rhyme"},
    "Song": {"Telugu": "పాట", "Hindi": "పాట", "English": "Song"},
    "Poem": {"Telugu": "గేయం", "Hindi": "కవిత", "English": "Poem"},
    "History": {"Telugu": "చరిత్ర", "Hindi": "చరిత్ర", "English": "History"},
    "Other": {"Telugu": "ఇతర", "Hindi": "ఇతర", "English": "Other"}
}

def get_translated_genre(genre_key, language):
    """Returns the genre in the target language or defaults to English."""
    if language not in ["Telugu", "Hindi"]:
        return genre_key # Default to English for others for now

    return GENRE_MAP.get(genre_key, {}).get(language, genre_key)

def display_json_result(result):
    if result.get("status") == "success":
        st.success(f"Status: {result.get('status')}")
    elif result.get("status") == "failure":
        st.error(f"Status: {result.get('status')}")
    else:
        st.warning(f"Status: {result.get('status')}")

    st.json(result)

def get_mock_response(agent_type):
    if agent_type == "validation":
        return {
            "is_coherent": True,
            "is_meaningful": True,
            "is_appropriate": True,
            "is_valuable": True,
            "overall_valid": True,
            "rejection_reason": None
        }
    elif agent_type == "metadata":
        return {
            "title": "Mock Title",
            "keywords": ["mock", "test"],
            "genre": "FOLKLORE",
            "theme": "Testing",
            "moral": "Testing is good",
            "characters": ["Tester"],
            "locations": ["Localhost"],
            "summary": "This is a mock summary."
        }
    return {}

# --- Main App Logic ---

st.title("🐘 Chandamama Agentic Engine")

# Tabs for Mode Selection
tab1, tab2, tab3 = st.tabs(["Contribute Story (Agent 1)", "Metadata Generation (Agent 2)", "Full Workflow"])

with tab1:
    st.subheader("Contribution Portal")
    st.markdown("Please enter the story details below. **Title** and **Story Text** are mandatory.")

    col1, col2 = st.columns([1, 1])

    with col1:
        with st.form("contribution_form"):
            # Language Dropdown with specific order
            languages = [
                "Telugu", "Hindi", "English", "Tamil", "Malayalam",
                "Kannada", "Tulu", "Konkani", "Kodava"
            ]
            language = st.selectbox("Language *", languages)

            title = st.text_input("Story Title *", placeholder="Enter the title in Telugu or English...")

            # Additional Metadata Fields
            col_a, col_b = st.columns(2)
            with col_a:
                author = st.text_input("Author (Optional)")
                genre_options = ["Folklore", "Mythology", "Moral Story", "Nursery Rhyme", "Song", "Poem", "History", "Other"]
                genre = st.selectbox("Genre (Optional)", genre_options, index=2)
                source_year = st.number_input("Source Year (Optional)", min_value=1900, max_value=2024, value=None, placeholder="e.g. 1948")

            with col_b:
                target_age = st.selectbox("Target Age Group (Optional)", ["Children (3-8)", "Pre-Teens (9-12)", "Teens (13+)", "General Audience"], index=1)
                keywords = st.text_input("Keywords (comma separated)", placeholder="e.g. magic, king, animals")
                illustrator = st.text_input("Illustrator (Optional)")

            moral = st.text_input("Moral (Optional)")
            story_text = st.text_area("Story Text *", height=300, placeholder="Paste the full Telugu story here...")

            submitted = st.form_submit_button("Validate & Contribute")

    if submitted:
        if not title.strip():
            st.error("Title is required!")
        elif not story_text.strip():
            st.error("Story text is required!")
        else:
            # Construct User Fields with Timestamp and Language
            user_fields = {
                "title": title,
                "language": language,
                "contribution_timestamp": datetime.now().isoformat(),
                "genre": get_translated_genre(genre, language), # Map to Tel/Hindi
                "target_age_group": target_age
            }
            if author.strip(): user_fields["author"] = author
            if moral.strip(): user_fields["moral"] = moral
            if keywords.strip(): user_fields["keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]
            if illustrator.strip(): user_fields["illustrator"] = illustrator
            if source_year: user_fields["source_year"] = source_year

            agent = StoryValidationAgent()
            payload = {"story_text": story_text, "user_fields": user_fields}

            with st.spinner("Validating Story Content..."):
                if mock_llm:
                    with patch('agentic_engine.agents.story_validation_agent.generate_json_response', return_value=get_mock_response("validation")):
                        result = agent.process(payload)
                else:
                    result = agent.process(payload)

            with col2:
                st.subheader("Validation Result")
                display_json_result(result)


with tab2:
    st.subheader("Metadata Extractor")

    col1, col2 = st.columns([1, 1])

    with col1:
        source_type = st.selectbox("Source Type", ["story", "prompt"])

        # Language Dropdown
        languages = [
            "Telugu", "Hindi", "English", "Tamil", "Malayalam",
            "Kannada", "Tulu", "Konkani", "Kodava"
        ]
        meta_language = st.selectbox("Language (for Extraction)", languages)

        input_text = st.text_area("Input Text", height=300, placeholder="Enter story or prompt text...")
        user_fields_str = st.text_area("User Fields (JSON)", height=150, value='{"source_reference": "1980-05"}', placeholder='{"genre": "..."}')

    if st.button("Generate Metadata"):
        try:
            user_fields = json.loads(user_fields_str)
            user_fields["language"] = meta_language  # Inject selected language

            agent = MetadataGenerationAgent()

            payload = {
                "source": source_type,
                "text": input_text,
                "user_fields": user_fields
            }

            with st.spinner("Extracting Metadata..."):
                if mock_llm:
                    with patch('agentic_engine.llm_client.generate_json_response', return_value=get_mock_response("metadata")):
                        result = agent.process(payload)
                else:
                    result = agent.process(payload)

            with col2:
                st.subheader("Metadata Result")
                display_json_result(result)

        except json.JSONDecodeError:
            st.error("Invalid JSON in User Fields")
        except Exception as e:
            st.error(f"Error: {str(e)}")

with tab3:
    st.subheader("Ingestion Workflow Check")

    st.markdown("Simulates the full pipeline: Contribution -> Validation -> Metadata Extraction")

    with st.form("workflow_form"):
        # Language Dropdown in Workflow
        languages = [
            "Telugu", "Hindi", "English", "Tamil", "Malayalam",
            "Kannada", "Tulu", "Konkani", "Kodava"
        ]
        language = st.selectbox("Language *", languages)

        title = st.text_input("Story Title *")

        # Additional Metadata Fields
        col_wf1, col_wf2 = st.columns(2)
        with col_wf1:
            author = st.text_input("Author (Optional)")
            genre_options = ["Folklore", "Mythology", "Moral Story", "Nursery Rhyme", "Song", "Poem", "History", "Other"]
            genre = st.selectbox("Genre (Optional)", genre_options, index=2)
            source_year = st.number_input("Source Year (Optional)", min_value=1900, max_value=2024, value=None, placeholder="e.g. 1948")

        with col_wf2:
            target_age = st.selectbox("Target Age Group (Optional)", ["Children (3-8)", "Pre-Teens (9-12)", "Teens (13+)", "General Audience"], index=1)
            keywords = st.text_input("Keywords (comma separated)", placeholder="e.g. magic, king, animals")
            illustrator = st.text_input("Illustrator (Optional)")

        moral = st.text_input("Moral (Optional)")
        story_text = st.text_area("Story Text *", height=300)
        submitted = st.form_submit_button("Run Workflow")

    if submitted:
        if not title or not story_text:
            st.error("Title and Story Text are required.")
        else:
            st.info("Starting Workflow...")

            # --- Step 1 ---
            st.markdown("### Step 1: Validation Agent")
            val_agent = StoryValidationAgent()

            # Construct user_fields with language and timestamp
            user_fields = {
                "title": title,
                "language": language,
                "contribution_timestamp": datetime.now().isoformat(),
                "genre": get_translated_genre(genre, language), # Map to Tel/Hindi
                "target_age_group": target_age
            }
            if author.strip(): user_fields["author"] = author
            if moral.strip(): user_fields["moral"] = moral
            if keywords.strip(): user_fields["keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]
            if illustrator.strip(): user_fields["illustrator"] = illustrator
            if source_year: user_fields["source_year"] = source_year

            val_payload = {
                "story_text": story_text,
                "user_fields": user_fields
            }

            if mock_llm:
                with patch('agentic_engine.agents.story_validation_agent.generate_json_response', return_value=get_mock_response("validation")):
                    val_result = val_agent.process(val_payload)
            else:
                val_result = val_agent.process(val_payload)

            display_json_result(val_result)

            if val_result["status"] == "success":
                # --- Step 2 ---
                st.markdown("### Step 2: Metadata Agent")
                meta_agent = MetadataGenerationAgent()

                # Pass validated text to metadata agent
                meta_payload = {
                    "source": "story",
                    "text": val_result["payload"]["validated_story"],
                    "user_fields": val_result["payload"]["user_fields"]
                }

                if mock_llm:
                    with patch('agentic_engine.agents.metadata_generation_agent.generate_json_response', return_value=get_mock_response("metadata")):
                        meta_result = meta_agent.process(meta_payload)
                else:
                    meta_result = meta_agent.process(meta_payload)

                display_json_result(meta_result)

                st.success("Workflow Completed Successfully!")
            else:
                st.error("Workflow Halted at Validation Step.")
