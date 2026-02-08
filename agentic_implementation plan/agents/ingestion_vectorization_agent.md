# Ingestion & Vectorization Agent

> **Agent 3 of Workflow 1: Ingestion & Knowledge Building**

---

## Purpose

Store validated stories and their embeddings in the vector database (Qdrant Cloud) and structured metadata in Supabase. This is a **script-only agent** with NO LLM calls.

---

## Why It Exists

| Problem | Solution |
|---------|----------|
| Manual embedding generation | Automated pipeline |
| Inconsistent storage formats | Standardized schema |
| Single storage backend | Hybrid Qdrant + Supabase |
| Slow sequential processing | Batch operations |
| No idempotency | Check-before-write logic |

---

## Inputs

```json
{
    "story_id": "uuid-v4",
    "title": "కథ పేరు",
    "author": "రచయిత",
    "year": 1975,
    "month": 3,
    "source_reference": "Chandamama 1975-03",
    "normalized_genre_code": "FOLKLORE",
    "content_type": "STORY",
    "keywords": ["keyword1", "keyword2"],
    "characters": ["char1", "char2"],
    "locations": ["loc1", "loc2"],
    "theme": "theme",
    "moral": "moral or null",
    "summary": "summary text",
    "language": "Telugu",
    "word_count": 450,
    "char_count": 2500,
    "text": "Full story content..."
}
```

---

## Outputs

### Success
```json
{
    "status": "success",
    "story_id": "uuid-v4",
    "qdrant_point_id": "uuid-v5",
    "supabase_row_id": 12345,
    "embedding_dimension": 768,
    "token_count": 1200
}
```

### Failure
```json
{
    "status": "failure",
    "error_code": "QDRANT_UPSERT_FAILED",
    "error_message": "Connection timeout after 3 retries",
    "partial_success": {
        "qdrant": false,
        "supabase": true
    }
}
```

---

## Processing Logic

### Step 1: Generate Embedding Text

```python
def compose_embedding_text(metadata: dict) -> str:
    """Compose rich text for embedding generation."""
    
    header_parts = []
    if metadata.get('title'):
        header_parts.append(f"Title: {metadata['title']}")
    if metadata.get('author'):
        header_parts.append(f"Author: {metadata['author']}")
    if metadata.get('keywords'):
        kws = metadata['keywords']
        if isinstance(kws, list):
            kws = ", ".join(kws)
        header_parts.append(f"Keywords: {kws}")
    
    header = "\n".join(header_parts)
    return f"{header}\n\n{metadata['text']}"
```

### Step 2: Create Embedding

```python
def generate_embedding(text: str) -> list[float]:
    """Generate 768-dim embedding using GTE model."""
    
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(
        "Alibaba-NLP/gte-multilingual-base",
        trust_remote_code=True
    )
    
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()
```

### Step 3: Store in Qdrant (Primary)

```python
def store_in_qdrant(story_id: str, embedding: list, metadata: dict):
    """Store embedding and full payload in Qdrant (primary store)."""
    
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    import uuid
    
    client = get_qdrant_client()
    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, story_id))
    
    # Full payload - Qdrant is the primary store
    payload = {
        "story_id": story_id,
        "title": metadata.get("title", ""),
        "author": metadata.get("author", ""),
        "year": metadata.get("year"),
        "month": metadata.get("month"),
        "normalized_genre_code": metadata.get("normalized_genre_code", ""),
        "keywords": metadata.get("keywords", []),
        "text": metadata.get("text", ""),  # Full text for RAG
    }
    
    client.upsert(
        collection_name="chandamama_stories",
        points=[models.PointStruct(
            id=point_id,
            vector=embedding,
            payload=payload
        )]
    )
    
    return point_id
```

### Step 4: Backup to Supabase (Weekly, Async)

> [!NOTE]
> Supabase is used for **backup only**, not live queries. This runs as a separate weekly job, not during ingestion.

```python
# This is NOT called during ingestion - it's a separate weekly cron job

async def weekly_backup_to_supabase():
    """Weekly backup job: Export Qdrant → Disk → Supabase."""
    
    # 1. Export all stories from Qdrant
    stories = export_all_from_qdrant()
    
    # 2. Save to local disk
    timestamp = datetime.now().strftime("%Y%m%d")
    backup_path = f"data/backups/stories_{timestamp}.json"
    with open(backup_path, "w") as f:
        json.dump(stories, f, ensure_ascii=False)
    
    # 3. Sync to Supabase
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    for story in stories:
        supabase.table("stories_backup").upsert(story).execute()
    
    print(f"Backed up {len(stories)} stories to Supabase")
```

---

## Failure Modes

| Failure Mode | Handling | Recovery |
|--------------|----------|----------|
| Qdrant timeout | Retry 3x with backoff | Queue for later |
| Supabase timeout | Retry 3x with backoff | Log, continue |
| Duplicate story_id | Skip (idempotent) | Return existing IDs |
| Token limit exceeded | Log, skip embedding | Store metadata only |
| Network error | Retry with exponential backoff | Queue for later |

---

## Cost Considerations

| Operation | Cost | Notes |
|-----------|------|-------|
| Embedding generation | ~0 | Self-hosted model |
| Qdrant upsert | ~0 | Free tier (500MB) |
| Supabase insert | ~0 | Free tier |
| Total per story | $0 | No external API costs |

---

## Reusability

| Workflow | Usage |
|----------|-------|
| **WF1: Ingestion** | Primary use case |
| **WF2: Generation** | Not used |

---

## Mapping to Existing Code

| Function | Existing Code | Status |
|----------|---------------|--------|
| Embedding composition | `story_embedder/embedder.py` (lines 35-48) | REUSE |
| Embedding generation | `story_embedder/embedder.py` (line 72) | REUSE |
| Qdrant storage | `story_embedder/storage.py` | REUSE |
| Supabase storage | None | NEW |

---

## Configuration

```python
# src/agents/ingestion_agent.py

class IngestionAgentConfig:
    EMBEDDING_MODEL = "Alibaba-NLP/gte-multilingual-base"
    MAX_TOKEN_LIMIT = 8192
    QDRANT_COLLECTION = "chandamama_stories"
    VECTOR_SIZE = 768
    RETRY_ATTEMPTS = 3
    RETRY_BACKOFF_SECONDS = [1, 3, 10]
    
    # Feature flag
    USE_SUPABASE = config.FEATURE_FLAGS.get("use_supabase_storage", False)
```

---

## Database Schema (Supabase)

```sql
CREATE TABLE stories (
    id SERIAL PRIMARY KEY,
    story_id UUID UNIQUE NOT NULL,
    title TEXT,
    author TEXT,
    year INTEGER,
    month INTEGER,
    source_reference TEXT,
    normalized_genre_code TEXT,
    content_type TEXT,
    keywords TEXT[],
    characters TEXT[],
    locations TEXT[],
    theme TEXT,
    moral TEXT,
    summary TEXT,
    language TEXT DEFAULT 'Telugu',
    word_count INTEGER,
    char_count INTEGER,
    telugu_ratio FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_stories_genre ON stories(normalized_genre_code);
CREATE INDEX idx_stories_year ON stories(year);
CREATE INDEX idx_stories_keywords ON stories USING GIN(keywords);
```

---

## Example Scenario

```
Input: Complete metadata object with 2500-char story

Step 1: Compose embedding text
  → "Title: వినయశీలుడు\nAuthor: విశ్వం\nKeywords: రాజు, వినయం\n\nఒకప్పుడు..."

Step 2: Generate embedding
  → [0.023, -0.045, 0.087, ...] (768 dimensions)
  → Token count: 1200 (within 8192 limit)

Step 3: Store in Qdrant
  → Point ID: "550e8400-e29b-41d4-..."
  → Payload: {story_id, title, text, year, month}

Step 4: Store in Supabase
  → Row ID: 12345
  → All metadata except text (22 fields)

Output: 
  status: "success"
  qdrant_point_id: "550e8400..."
  supabase_row_id: 12345

LLM Calls: 0
```
