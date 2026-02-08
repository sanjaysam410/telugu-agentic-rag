# Keyword Intelligence Agent

> **Agent 4 of Workflow 1: Ingestion & Knowledge Building (Async)**

---

## Purpose

Track keyword frequency across the archive using **TF-IDF scoring** and maintain ranked statistics for faceted search UI. Uses **incremental + nightly** update strategy.

---

## Why It Exists

| Problem | Solution |
|---------|----------|
| Popular keywords always dominate | TF-IDF surfaces distinctive terms |
| Static stats become stale | Incremental updates every 15 min |
| Expensive full recalculation | Nightly batch for heavy compute |
| No trending visibility | Trend tracking with 30-day delta |
| Blocking ingestion on stats | Async, non-blocking processing |

---

## Inputs

```json
{
    "story_id": "uuid-v4",
    "metadata": {
        "keywords": ["రాజు", "వినయం", "గర్వం"],
        "characters": ["రాజు", "మంత్రి"],
        "locations": ["రాజ్యం", "అడవి"],
        "normalized_genre_code": "MORAL_STORY",
        "author": "విశ్వం"
    }
}
```

---

## Outputs

No direct output (fire-and-forget async operation).

**Side Effects:**
- `data/stats/enhanced_stats.json` updated
- In-memory stats cache refreshed
- Co-occurrence matrix updated (nightly)

---

## TF-IDF Scoring (Strategy B)

### Formula

```
TF-IDF = TF × IDF

Where:
  TF (Term Frequency) = keyword_count / total_words_in_corpus
  IDF (Inverse Document Frequency) = log(total_stories / stories_containing_keyword)
```

### Implementation

```python
import math

def calculate_tfidf(keyword: str, stats: dict) -> float:
    """
    Calculate TF-IDF score for a keyword.
    
    Returns: float between 0-1 (higher = more distinctive)
    """
    corpus = stats["corpus_stats"]
    kw = stats["keywords"][keyword]
    
    # Term Frequency (normalized by corpus size)
    tf = kw["count"] / corpus["total_words"]
    
    # Inverse Document Frequency
    # Add 1 to avoid division by zero
    idf = math.log(corpus["total_stories"] / max(kw["document_frequency"], 1))
    
    # Raw TF-IDF
    raw_tfidf = tf * idf
    
    # Normalize to 0-1 range (empirical max ~0.001)
    normalized = min(raw_tfidf / 0.001, 1.0)
    
    return round(normalized, 4)
```

### Ranking Behavior

| Keyword | Count | Doc Freq | TF-IDF | Rank |
|---------|-------|----------|--------|------|
| రాజు | 1021 | 890 | 0.45 | Medium (common) |
| బంగారు లేడి | 45 | 42 | 0.78 | High (distinctive) |
| కథ | 5000 | 4900 | 0.12 | Low (too common) |

---

## Update Strategy: Incremental + Nightly

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    UPDATE STRATEGY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ON INGESTION (real-time):                                     │
│    → Increment counts in memory                                │
│    → Mark keywords as "dirty"                                  │
│                                                                 │
│  EVERY 15 MINUTES (cron):                                      │
│    → Persist dirty keywords to enhanced_stats.json             │
│    → Update document frequencies                               │
│    → Clear dirty flags                                         │
│                                                                 │
│  NIGHTLY @ 2 AM (cron):                                        │
│    → Full TF-IDF recalculation                                 │
│    → Re-rank all keywords                                      │
│    → Calculate trends (30-day delta)                           │
│    → Rebuild co-occurrence matrix                              │
│    → Generate trending keywords list                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Processing Logic

### Step 1: Real-Time Ingestion Update (Async)

```python
import threading
from collections import defaultdict

# Thread-safe dirty tracking
_lock = threading.Lock()
_dirty_keywords = set()
_pending_updates = defaultdict(lambda: {"count": 0, "doc_freq": 0})

def on_story_ingested(metadata: dict):
    """Called immediately after story ingestion. Non-blocking."""
    
    keywords = metadata.get("keywords", [])
    characters = metadata.get("characters", [])
    locations = metadata.get("locations", [])
    
    with _lock:
        for keyword in keywords:
            _pending_updates[keyword]["count"] += 1
            _pending_updates[keyword]["doc_freq"] += 1
            _dirty_keywords.add(keyword)
        
        # Similar for characters and locations...
    
    # Fire-and-forget: schedule async persistence
    schedule_incremental_update()
```

### Step 2: Incremental Persistence (Every 15 min)

```python
def incremental_update():
    """Persist pending updates. Runs every 15 minutes."""
    
    global _dirty_keywords, _pending_updates
    
    with _lock:
        if not _dirty_keywords:
            return  # Nothing to update
        
        dirty = _dirty_keywords.copy()
        updates = dict(_pending_updates)
        _dirty_keywords.clear()
        _pending_updates.clear()
    
    # Load current stats
    stats = load_enhanced_stats()
    
    # Apply updates
    for keyword, delta in updates.items():
        if keyword not in stats["keywords"]:
            stats["keywords"][keyword] = {
                "count": 0,
                "document_frequency": 0,
                "tfidf_score": 0,
                "rank": len(stats["keywords"]) + 1,
                "percentile": 0,
                "last_seen": today(),
                "trend": "new",
                "trend_delta": 0
            }
        
        stats["keywords"][keyword]["count"] += delta["count"]
        stats["keywords"][keyword]["document_frequency"] += delta["doc_freq"]
        stats["keywords"][keyword]["last_seen"] = today()
    
    # Update corpus stats
    stats["corpus_stats"]["total_stories"] += len(updates)
    stats["last_incremental_update"] = now()
    
    # Save
    save_enhanced_stats(stats)
    print(f"Incremental update: {len(dirty)} keywords updated")
```

### Step 3: Nightly Full Recalculation (2 AM)

```python
def nightly_full_recalculation():
    """Complete recalculation. Runs at 2 AM daily."""
    
    print("Starting nightly full recalculation...")
    stats = load_enhanced_stats()
    
    # 1. Recalculate ALL TF-IDF scores
    for keyword in stats["keywords"]:
        stats["keywords"][keyword]["tfidf_score"] = \
            calculate_tfidf(keyword, stats)
    
    # 2. Sort and rank by TF-IDF (descending)
    sorted_keywords = sorted(
        stats["keywords"].items(),
        key=lambda x: x[1]["tfidf_score"],
        reverse=True
    )
    
    total = len(sorted_keywords)
    for rank, (keyword, data) in enumerate(sorted_keywords, 1):
        old_rank = data.get("rank", rank)
        
        data["rank"] = rank
        data["percentile"] = round((1 - rank/total) * 100, 1)
        
        # Calculate trend (30-day window)
        delta = old_rank - rank
        data["trend_delta"] = delta
        
        if delta > 10:
            data["trend"] = "up"
        elif delta < -10:
            data["trend"] = "down"
        else:
            data["trend"] = "stable"
    
    # 3. Rebuild co-occurrence matrix
    stats["co_occurrence_matrix"] = build_co_occurrence_matrix()
    
    # 4. Generate trending lists
    rising = sorted(
        [(k, d["trend_delta"]) for k, d in stats["keywords"].items() 
         if d["trend_delta"] > 10],
        key=lambda x: x[1],
        reverse=True
    )[:20]
    
    falling = sorted(
        [(k, d["trend_delta"]) for k, d in stats["keywords"].items() 
         if d["trend_delta"] < -10],
        key=lambda x: x[1]
    )[:10]
    
    stats["trending"] = {
        "rising": [{"keyword": k, "delta": d} for k, d in rising],
        "falling": [{"keyword": k, "delta": d} for k, d in falling]
    }
    
    stats["generated_at"] = now()
    save_enhanced_stats(stats)
    
    print(f"Nightly recalc complete: {total} keywords ranked")
```

---

## Co-Occurrence Matrix

Identifies keywords that frequently appear together:

```python
def build_co_occurrence_matrix(top_n: int = 500) -> dict:
    """Build keyword co-occurrence from Qdrant payloads."""
    
    from collections import Counter
    
    # Get top N keywords by frequency
    stats = load_enhanced_stats()
    top_keywords = sorted(
        stats["keywords"].items(),
        key=lambda x: x[1]["count"],
        reverse=True
    )[:top_n]
    top_set = {k for k, _ in top_keywords}
    
    # Scan all stories from Qdrant
    co_occur = defaultdict(Counter)
    
    for story in fetch_all_story_keywords():  # From Qdrant
        keywords = story.get("keywords", [])
        for kw in keywords:
            if kw in top_set:
                for other in keywords:
                    if other != kw and other in top_set:
                        co_occur[kw][other] += 1
    
    # Convert to top-5 co-occurring for each
    matrix = {}
    for kw, counter in co_occur.items():
        matrix[kw] = [k for k, _ in counter.most_common(5)]
    
    return {"keywords": matrix}
```

---

## Cron Schedule

```bash
# crontab entries

# Incremental update every 15 minutes
*/15 * * * * /path/to/python -m agents.keyword_agent incremental

# Nightly full recalculation at 2 AM
0 2 * * * /path/to/python -m agents.keyword_agent nightly
```

---

## Configuration

```python
# src/agents/keyword_agent.py

class KeywordAgentConfig:
    # Update intervals
    INCREMENTAL_INTERVAL_MINUTES = 15
    NIGHTLY_HOUR = 2  # 2 AM
    
    # Ranking
    TFIDF_NORMALIZATION_FACTOR = 0.001
    TREND_THRESHOLD = 10  # Rank delta to trigger trend change
    
    # Limits
    MAX_KEYWORDS_TO_RANK = 10000
    MAX_CO_OCCURRENCE_KEYWORDS = 500
    TOP_TRENDING_COUNT = 20
    
    # Storage
    STATS_FILE = "data/stats/enhanced_stats.json"
    LEGACY_STATS_FILE = "data/stats/global_stats.json"
```

---

## Example Scenario

```
Day 1: New story ingested with keywords ["బంగారు లేడి", "అడవి", "జింక"]

Immediate (async):
  → _dirty_keywords.add("బంగారు లేడి", "అడవి", "జింక")
  → _pending_updates incremented

15-minute cron:
  → enhanced_stats.json updated:
      "బంగారు లేడి": {count: 46, doc_freq: 43, ...}
  → Dirty flags cleared

2 AM nightly:
  → TF-IDF recalculated:
      "బంగారు లేడి" tfidf: 0.78 (high - rare term)
      "అడవి" tfidf: 0.42 (medium - common)
  → Rankings updated
  → Co-occurrence: "బంగారు లేడి" often appears with ["అడవి", "జింక", "రాజు"]
  → Trend: "బంగారు లేడి" trend_delta: +3 (stable)
```

---

## Failure Handling

| Failure | Handling |
|---------|----------|
| Incremental cron fails | Dirty flags retained, next run catches up |
| Nightly cron fails | Alert, manual rerun, stats stale until next night |
| Stats file corrupt | Load from backup, regenerate from Qdrant |
| Memory overflow | Process keywords in batches |

---

## Backward Compatibility

Generates both files:
- `enhanced_stats.json` - New format with TF-IDF
- `global_stats.json` - Legacy format for existing UI

```python
def sync_legacy_stats():
    """Keep legacy format in sync for backward compat."""
    
    enhanced = load_enhanced_stats()
    
    legacy = {
        "total_stories": enhanced["corpus_stats"]["total_stories"],
        "keywords": {k: d["count"] for k, d in enhanced["keywords"].items()},
        "characters": {k: d["count"] for k, d in enhanced["characters"].items()},
        "locations": {k: d["count"] for k, d in enhanced["locations"].items()},
        "authors": {k: d["count"] for k, d in enhanced["authors"].items()}
    }
    
    with open("data/stats/global_stats.json", "w") as f:
        json.dump(legacy, f, ensure_ascii=False, indent=2)
```
