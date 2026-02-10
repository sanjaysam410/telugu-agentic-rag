import time
from typing import Dict, Any, Generator
from langchain_core.messages import SystemMessage, HumanMessage

from src.config import get_reasoning_llm, Config
from src.utils.story_constants import (
    GENRE_ADDITIONS,
    TONE_ADDITIONS,
    KEYWORD_INTEGRATION_LOGIC,
    ANTI_REPETITION_RULES
)

def generate_story(facets: Dict[str, Any], context_text: str = "") -> Generator[str, None, None]:
    """
    Generates a NEW, ORIGINAL Telugu story based on user facets and RAG context.
    Adapted from Chandamama Studio for Agentic RAG.
    Returns a generator handling streaming tokens.
    """

    # Extract facets with defaults
    genre = facets.get("genre", "Folklore")
    keywords = facets.get("keywords", [])
    chars = facets.get("characters", [])
    locations = facets.get("locations", [])

    # New facets
    content_type = facets.get("content_type", "SINGLE")
    num_chapters = facets.get("num_chapters", 1)

    # Format lists for prompt
    keywords_str = ", ".join(keywords) if keywords else "None"
    chars_str = ", ".join(chars) if chars else "Generic Characters"
    locations_str = ", ".join(locations) if locations else "Generic Village"

    # User's custom prompt
    custom_instruction = facets.get("prompt_input", "").strip()

    # Determine derived variables (Shared logic)
    genre_key = genre.lower().replace(" ", "_")

    # Add Tone if present in facets
    tone = facets.get("tone", "traditional")
    tone_instruction = TONE_ADDITIONS.get(tone.lower(), "")

    # Add Genre specific guidelines
    genre_guidelines = GENRE_ADDITIONS.get(genre_key, "")

    # Force SINGLE story format
    content_type = "SINGLE"

    # Calculate derived variables
    length_setting = facets.get("length", "Medium")
    word_count_map = {
        "Short": "300-500",
        "Medium": "600-800",
        "Long": "1000-1500"
    }
    word_count = word_count_map.get(length_setting, "600-800")

    # Determine format based on genre
    ending_format = ""

    if "moral" in genre_key or "children" in genre_key or "folklore" in genre_key:
            ending_format = "Moral:\n<One clear sentence>"

    # CORE SYSTEM PROMPT (User-Provided English Structure with Translation Safeguards)
    prompt = f"""
You are an expert Telugu storyteller who writes engaging, well-crafted stories.

==================================================
ARCHIVE CONTEXT (STYLE REFERENCE)
==================================================
Learn narrative rhythm, vocabulary, and flow from these examples.
DO NOT copy plots or characters.

{context_text}

==================================================
STORY REQUEST
==================================================
Genre: {genre}
Themes/Keywords: {keywords_str}
Characters: {chars_str}
Setting: {locations_str}
Additional Instructions: {custom_instruction if custom_instruction else "Create an engaging story."}

Use these as creative inspiration—integrate naturally, don't force.

{genre_guidelines}

**TONE:** {tone_instruction}

==================================================
UNIVERSAL QUALITY STANDARDS (CRITICAL)
==================================================

**THINK IN TELUGU:**
- **DO NOT TRANSLATE FROM ENGLISH.**
- Use native Telugu idioms and sentence structures exclusively.

**CHARACTER DEVELOPMENT:**
- Give each character distinct personality (2-3 traits)
- Show personality through actions, speech, reactions
- Motivations must be clear and consistent
- Keep cast manageable (3-5 main characters)

**PLOT LOGIC:**
- Every event must have clear cause-effect
- Character choices should make sense from their perspective
- No convenient coincidences solving problems
- Physical actions must be visualizable
- Test: "Can I explain this to someone clearly?"

**NATURAL DIALOGUE:**
- Minimize dialogue tags (aim for 20-30% of lines)
- Use action beats and context to show speakers
- Let characters speak distinctly based on personality
- Mix dialogue with narrative flow

**SHOW, DON'T TELL:**
- Reveal emotions through physical reactions, not statements
- Let actions demonstrate character traits
- Use sensory details to create immersion

**WRITING QUALITY:**
- Vary sentence structure and length
- No phrase repetition (max 2 uses)
- **Natural Telugu flow, not translated English** (Avoiding passive voice/bookish terms)
- Appropriate vocabulary for target audience
- Consistent verb tenses

**STRUCTURE:**
- Clear beginning (setup + hook)
- Rising tension (conflict/challenge)
- Climax (decision/turning point)
- Resolution (earned consequences)
- Satisfying conclusion

{KEYWORD_INTEGRATION_LOGIC}

{ANTI_REPETITION_RULES}

==================================================
SELF-REVISION CHECKLIST
==================================================
Before finalizing:
□ Plot logic is sound and visualizable?
□ Each character has distinct personality?
□ Less than 30% dialogue has tags?
□ Emotions shown through action, not stated?
□ No repeated phrases or patterns?
□ Story flows naturally when read aloud?
□ Genre and tone appropriate throughout?

==================================================
OUTPUT FORMAT
==================================================
Title:
<Appropriate to genre and tone>

Story:
<Full Telugu story, {word_count} words>

{ending_format}

Label:
ఈ కథ కొత్తగా రూపొందించబడింది (Inspired by Archive).
"""

    # Call LLM with streaming using Config
    try:
        # Increased temperature for creativity
        llm = get_reasoning_llm(temperature=0.8)
        # We invoke stream
        stream = llm.stream([
            SystemMessage(content="You are a creative storyteller."),
            HumanMessage(content=prompt)
        ])

        full_text = ""
        for chunk in stream:
            content = chunk.content
            if content:
                full_text += content
                yield content

        # Append Label
        if "AI Generated" not in full_text:
            label = "\n\n(ఈ కథ కొత్తగా రూపొందించబడింది - AI Generated)"
            yield label

    except Exception as e:
        yield f"Error generating story: {str(e)}"
