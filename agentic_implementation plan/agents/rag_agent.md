# RAG Agent

> **Agent 3 of Workflow 2: Story Generation**

---

## Purpose

Retrieve relevant context from the vector database and generate new Telugu stories using the existing prompt engineering logic. This is the core "brain" of story generation.

---

## Why It Exists

| Problem | Solution |
|---------|----------|
| Stories need cultural grounding | RAG from Chandamama archive |
| Pure LLM may hallucinate | Context-grounded generation |
| Duplicate story plots | Retrieve existing, create new |
| Inconsistent style | Archive examples as templates |
| Complex prompt logic | Centralized agent |

---

## Inputs

```json
{
    "telugu_prompt": "అహంకారి రాజు వినయం నేర్చుకున్న కథ...",
    "metadata": {
        "keywords": ["రాజు", "వినయం"],
        "normalized_genre_code": "MORAL_STORY",
        "theme": "character transformation",
        "characters_inferred": ["రాజు"],
        "locations_inferred": ["రాజ్యం"]
    },
    "user_facets": {
        "genre": "Moral Story",
        "tone": "traditional",
        "content_type": "SINGLE",
        "num_chapters": 1
    },
    "feedback": null  // Or regeneration feedback from Validator Agent
}
```

---

## Outputs

```json
{
    "draft_story": "Title: వినయశీలుడు\n\nఒకప్పుడు ఒక రాజ్యంలో...",
    "context_stories_used": [
        {"story_id": "xyz", "title": "గర్వం పతనం", "year": 1965},
        {"story_id": "abc", "title": "వినయశీలుడు", "year": 1972}
    ],
    "generation_metadata": {
        "model": "openai/gpt-oss-120b",
        "tokens_generated": 2800,
        "temperature": 0.7,
        "context_token_count": 4500
    },
    "attempt_number": 1
}
```

---

## Processing Logic

### Step 1: Vector Search (Script)

```python
def retrieve_context(prompt: str, keywords: list, top_k: int = 3) -> str:
    """Retrieve relevant stories from Qdrant."""
    
    # Compose enriched search query
    keyword_str = " ".join(keywords) if keywords else ""
    search_query = f"{prompt} {keyword_str}".strip()
    
    # Use existing retriever
    from src.retrieval.vector_search import StoryEmbeddingsRetriever
    retriever = StoryEmbeddingsRetriever(top_k=top_k)
    
    # Get formatted context
    context = retriever.retrieve(search_query)
    return context
```

**Context Format (from existing code):**
```
### Story 1: వినయశీలుడు రాజు (ID: xyz, Date: 1965-07)
ఒకప్పుడు ఒక రాజ్యంలో ఒక అహంకారి రాజు ఉండేవాడు...
[Full story text]

### Story 2: గర్వం పతనం (ID: abc, Date: 1972-03)
ఒక గొప్ప రాజు తన గర్వం వల్ల...
[Full story text]
```

### Step 2: LLM Generation

**Reuses existing prompt templates from `src/story_gen.py`:**

```python
def generate_story(facets: dict, context: str, feedback: dict = None) -> str:
    """Generate story using existing logic + optional feedback."""
    
    from src.story_gen import generate_story as gen_story
    
    # Augment facets with regeneration feedback if present
    if feedback:
        facets["prompt_input"] = augment_with_feedback(
            facets.get("prompt_input", ""),
            feedback
        )
    
    # Stream story generation
    full_story = ""
    for chunk in gen_story(facets, context_text=context):
        full_story += chunk
        yield chunk  # For streaming to UI
    
    return full_story

def augment_with_feedback(original_prompt: str, feedback: dict) -> str:
    """Add specific improvement instructions."""
    
    issues = feedback.get("issues", [])
    fixes = feedback.get("specific_fixes", [])
    
    augmented = f"{original_prompt}\n\nIMPORTANT CORRECTIONS:\n"
    for fix in fixes:
        augmented += f"- {fix}\n"
    
    return augmented
```

---

## Prompt Template Reference

The agent uses these templates from `src/story_gen.py`:

| Template | Purpose |
|----------|---------|
| `GENRE_ADDITIONS` | Genre-specific guidelines |
| `TONE_ADDITIONS` | Tone instructions |
| `KEYWORD_INTEGRATION_LOGIC` | Keyword handling rules |
| `ANTI_REPETITION_RULES` | Quality writing rules |

**Single Story Prompt Structure:**
```
You are an expert Telugu storyteller...

==================================================
ARCHIVE CONTEXT (STYLE REFERENCE)
==================================================
{context}

==================================================
STORY REQUEST
==================================================
Genre: {genre}
Themes/Keywords: {keywords}
Characters: {characters}
...

{genre_guidelines}
{tone_instructions}
{keyword_logic}
{anti_repetition_rules}

==================================================
OUTPUT FORMAT
==================================================
Title: <Title>
Story: <Full story>
Moral: <If applicable>
```

---

## Failure Modes

| Failure Mode | Handling | User Impact |
|--------------|----------|-------------|
| Empty context | Proceed with LLM knowledge only | Warning shown |
| LLM timeout | Retry 2x, then fail gracefully | Error message |
| Context too long | Truncate to fit context window | Slightly degraded |
| Generation stream fails | Return partial + error | Incomplete story |

---

## Cost Considerations

| Operation | LLM Calls | Notes |
|-----------|-----------|-------|
| Vector search | 0 | Embedding model (local) |
| Story generation | 1 | Main cost |
| Regeneration attempt | +1 each | Max 2 retries |

**Token Budget (per generation):**
- Context: ~4000-6000 tokens
- Generation: ~2000-3000 tokens
- Total: ~7000-9000 tokens/generation

---

## Reusability

| Workflow | Usage |
|----------|-------|
| **WF1: Ingestion** | Not used |
| **WF2: Generation** | Primary use case |

---

## Mapping to Existing Code

| Function | Existing Code | Status |
|----------|---------------|--------|
| Vector search | `src/retrieval/vector_search.py` | REUSE (wrap) |
| Story generation | `src/story_gen.py` | REUSE (wrap) |
| Prompt templates | `src/story_gen.py` | REUSE (import) |
| LLM call | `src/local_llm_multi.py` | REUSE |
| Streaming | `src/story_gen.py` (lines 403-420) | REUSE |

---

## Configuration

```python
# src/agents/rag_agent.py

class RAGAgentConfig:
    TOP_K_RETRIEVAL = 3
    MAX_CONTEXT_TOKENS = 6000
    GENERATION_TEMPERATURE = 0.7
    MAX_GENERATION_TOKENS = 3500
    
    # Regeneration settings
    MAX_REGENERATION_ATTEMPTS = 3
    
    # Model selection
    DEFAULT_MODEL = "openai/gpt-oss-120b"
```

---

## Regeneration Flow

When the Validator Agent returns feedback:

```python
def handle_regeneration(feedback: dict, attempt: int) -> dict:
    """Process regeneration request."""
    
    if attempt >= MAX_REGENERATION_ATTEMPTS:
        raise MaxRetriesExceeded()
    
    # Augment prompt with specific fixes
    enhanced_facets = {
        **original_facets,
        "prompt_input": f"{original_prompt}\n\nFIX THESE ISSUES:\n" + 
                        "\n".join(feedback["specific_fixes"])
    }
    
    # Regenerate with feedback
    return generate_story(enhanced_facets, context)
```

---

## Example Scenario

```
Input:
  telugu_prompt: "తెలివైన రైతు కథ"
  metadata: {keywords: ["రైతు", "తెలివి"], genre: "FOLKLORE"}
  facets: {tone: "traditional", content_type: "SINGLE"}

Step 1: Vector Search
  Query: "తెలివైన రైతు కథ రైతు తెలివి"
  Retrieved: 3 stories about clever farmers (IDs: a1, b2, c3)

Step 2: LLM Generation
  Model: openai/gpt-oss-120b
  Temperature: 0.7
  
Output:
  draft_story: "Title: బుద్ధిమంతుడు రైతు\n\nఒకప్పుడు..."
  context_used: ["a1", "b2", "c3"]
  tokens: 2500

LLM Calls: 1
```
