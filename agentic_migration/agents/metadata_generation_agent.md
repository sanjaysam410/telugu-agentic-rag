# Metadata Generation Agent

> **Agent 2 of Workflow 1 & Agent 2 of Workflow 2 (REUSABLE)**

---

## Purpose

Extract and generate complete metadata for stories (WF1) or prompts (WF2) using a cost-optimized two-step approach: script extraction for simple fields, LLM for semantic fields.

---

## Why It Exists

| Problem | Solution |
|---------|----------|
| Manual metadata entry is tedious | Auto-extract from content |
| Inconsistent metadata quality | Standardized extraction |
| LLM-only extraction is expensive | Two-step reduces costs |
| Some fields are simple to extract | Script handles counts, dates |
| Some fields require understanding | LLM handles themes, genre |

---

## Inputs

### For Story Ingestion (WF1)
```json
{
    "source": "story",
    "text": "Full story content...",
    "user_fields": {
        "author": "Optional known author",
        "source_reference": "Chandamama 1975-03",
        "content_type": "STORY"
    }
}
```

### For Prompt Extraction (WF2)
```json
{
    "source": "prompt",
    "text": "అహంకారి రాజు వినయం నేర్చుకున్న కథ...",
    "user_facets": {
        "genre": "Moral Story",
        "keywords": ["రాజు"]
    }
}
```

---

## Outputs

### Complete Metadata (WF1)
```json
{
    "story_id": "uuid-v4",
    "title": "వినయశీలుడు రాజు",
    "author": "రచయిత పేరు",
    "year": 1975,
    "month": 3,
    "source_reference": "Chandamama 1975-03",
    "normalized_genre_code": "MORAL_STORY",
    "content_type": "STORY",
    "keywords": ["రాజు", "వినయం", "గర్వం", "transformation"],
    "characters": ["రాజు", "మంత్రి", "రైతు"],
    "locations": ["రాజ్యం", "అడవి", "గ్రామం"],
    "theme": "నైతిక పరివర్తన",
    "moral": "గర్వం పతనానికి దారితీస్తుంది",
    "summary": "అహంకారి రాజు తన గర్వం వల్ల...",
    "language": "Telugu",
    "word_count": 450,
    "char_count": 2500,
    "sentence_count": 45,
    "paragraph_count": 12,
    "telugu_ratio": 0.95,
    "text": "Full story content..."
}
```

### In-Memory Metadata (WF2)
```json
{
    "keywords": ["రాజు", "వినయం", "గర్వం"],
    "normalized_genre_code": "MORAL_STORY",
    "theme": "character transformation",
    "characters_inferred": ["రాజు"],
    "locations_inferred": ["రాజ్యం"]
}
```

---

## Processing Logic

### Step 1: Script-Based Extraction

```python
def script_extraction(text: str, user_fields: dict) -> dict:
    """Extract simple, countable fields without LLM."""
    
    metadata = {}
    
    # Statistics
    metadata["word_count"] = len(text.split())
    metadata["char_count"] = len(text)
    metadata["sentence_count"] = len(re.findall(r'[.!?।]', text))
    metadata["paragraph_count"] = len(text.split('\n\n'))
    
    # Telugu ratio
    telugu_chars = len(re.findall(r'[\u0C00-\u0C7F]', text))
    metadata["telugu_ratio"] = telugu_chars / max(len(text), 1)
    
    # Parse source reference
    if source_ref := user_fields.get("source_reference"):
        match = re.search(r'(\d{4})-(\d{2})', source_ref)
        if match:
            metadata["year"] = int(match.group(1))
            metadata["month"] = int(match.group(2))
    
    # Generate story_id
    metadata["story_id"] = str(uuid.uuid4())
    
    # Passthrough user fields
    metadata["author"] = user_fields.get("author", "Unknown")
    metadata["content_type"] = user_fields.get("content_type", "STORY")
    metadata["source_reference"] = user_fields.get("source_reference", "")
    metadata["language"] = "Telugu"
    
    return metadata
```

### Step 2: LLM-Based Extraction

**LLM Prompt:**
```
You are a Telugu literature metadata extractor.

Analyze this Telugu content and extract metadata:

CONTENT:
{text}

CONTENT TYPE: {content_type}

EXTRACT THE FOLLOWING (in Telugu where applicable):

1. TITLE: Extract or generate an appropriate title
2. KEYWORDS: List 5-10 important keywords/themes (Telugu)
3. GENRE: Classify as one of:
   - FOLKLORE, MYTHOLOGY, MORAL_STORY, CHILDREN_STORY
   - COMEDY, ADVENTURE, MYSTERY, SCIENCE, ROMANCE
   - PUZZLE, POEM, SONG, SERIAL, OTHER
4. THEME: Primary theme in 2-3 words
5. MORAL: If a moral story, extract the moral (1 sentence)
6. CHARACTERS: List all character names mentioned
7. LOCATIONS: List all location/place names
8. SUMMARY: 2-3 sentence summary (Telugu)

OUTPUT FORMAT (JSON only):
{
    "title": "కథ పేరు",
    "keywords": ["keyword1", "keyword2", ...],
    "normalized_genre_code": "GENRE_CODE",
    "theme": "థీమ్",
    "moral": "నీతి వాక్యం" or null,
    "characters": ["పేరు1", "పేరు2"],
    "locations": ["ప్రదేశం1", "ప్రదేశం2"],
    "summary": "సంక్షిప్త వివరణ..."
}
```

---

## Failure Modes

| Failure Mode | Handling | Impact |
|--------------|----------|--------|
| LLM timeout | Retry 3x, use partial metadata | Degraded quality |
| LLM returns invalid JSON | Parse best-effort, log error | Degraded quality |
| Missing fields | Use defaults, flag for review | Functional |
| Source reference unparseable | Skip year/month, log | Functional |

---

## Cost Considerations

| Scenario | LLM Calls | Notes |
|----------|-----------|-------|
| Story with user facets | 1 | Full semantic extraction |
| Prompt with complete facets | 0 | Script merge only |
| Prompt with sparse facets | 1 | Infer missing fields |

**Optimization Notes:**
- Batch multiple stories in single LLM call (future)
- Cache common patterns (keywords → genre mapping)
- Skip LLM if user provides all semantic fields

---

## Reusability

| Workflow | Usage | Mode |
|----------|-------|------|
| **WF1: Ingestion** | Full metadata generation | Store to DB |
| **WF2: Generation** | Prompt metadata extraction | In-memory only |

**Behavioral Differences:**
```python
if source == "story":
    # Full extraction, store everything
    return complete_metadata
elif source == "prompt":
    # Minimal extraction for RAG enhancement
    return {
        "keywords": extracted.keywords + user_facets.keywords,
        "genre": extracted.genre or user_facets.genre,
        "theme": extracted.theme
    }
```

---

## Mapping to Existing Code

| Function | Existing Code | Status |
|----------|---------------|--------|
| Stats extraction | None | NEW: Script logic |
| Source parsing | `generate_chunks.py` (line 140-151) | REFERENCE |
| LLM call | `src/local_llm_multi.py` | REUSE |
| Keyword handling | `story_gen.py` (KEYWORD_INTEGRATION_LOGIC) | REFERENCE |

---

## Configuration

```python
# src/agents/metadata_agent.py

class MetadataAgentConfig:
    MAX_KEYWORDS = 10
    MIN_KEYWORDS = 5
    LLM_TIMEOUT_SECONDS = 45
    
    GENRE_CODES = [
        "FOLKLORE", "MYTHOLOGY", "MORAL_STORY", "CHILDREN_STORY",
        "COMEDY", "ADVENTURE", "MYSTERY", "SCIENCE", "ROMANCE",
        "PUZZLE", "POEM", "SONG", "SERIAL", "OTHER"
    ]
    
    # Feature flag
    ENABLED = config.FEATURE_FLAGS.get("use_metadata_agent", False)
```

---

## Example Scenarios

### Scenario 1: Full Story Ingestion
```
Input: 
  source: "story"
  text: "ఒకప్పుడు ఒక అడవిలో..."
  user_fields: {author: "విశ్వం", source_reference: "1965-07"}

Step 1 Output:
  word_count: 450, year: 1965, month: 7, ...

Step 2 Output:
  title: "అడవి రాజు", genre: "FOLKLORE", keywords: [...], ...

Final: Complete 20-field metadata object
LLM Calls: 1
```

### Scenario 2: Prompt with Complete Facets (WF2)
```
Input:
  source: "prompt"
  text: "రాజు వినయం కథ"
  user_facets: {genre: "MORAL_STORY", keywords: ["రాజు", "వినయం"]}

Processing: Merge user facets, no LLM needed

Output: {keywords: ["రాజు", "వినయం"], genre: "MORAL_STORY"}
LLM Calls: 0
```

### Scenario 3: Prompt with Sparse Facets (WF2)
```
Input:
  source: "prompt"
  text: "అడవిలో బంగారు లేడి కథ చెప్పు"
  user_facets: {}

Processing: LLM infers keywords, genre

Output: {keywords: ["అడవి", "బంగారు లేడి"], genre: "FOLKLORE"}
LLM Calls: 1
```
