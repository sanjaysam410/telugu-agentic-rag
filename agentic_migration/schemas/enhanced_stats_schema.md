# Enhanced Stats Schema

> **Schema for `data/stats/enhanced_stats.json`**

---

## Overview

The enhanced stats file provides rich, ranked statistics for the faceted search UI with TF-IDF scoring, trend tracking, and co-occurrence data.

---

## Full Schema

```json
{
    "version": "2.0",
    "generated_at": "2026-02-08T17:00:00Z",
    "last_incremental_update": "2026-02-08T16:45:00Z",
    
    "corpus_stats": {
        "total_stories": 10212,
        "total_words": 4500000,
        "total_unique_keywords": 8500,
        "total_unique_characters": 3200,
        "total_unique_locations": 1800
    },
    
    "keywords": {
        "రాజు": {
            "count": 1021,
            "document_frequency": 890,
            "tfidf_score": 0.45,
            "rank": 1,
            "percentile": 99.5,
            "last_seen": "2026-02-08",
            "trend": "stable",
            "trend_delta": 0
        },
        "బంగారు లేడి": {
            "count": 45,
            "document_frequency": 42,
            "tfidf_score": 0.78,
            "rank": 250,
            "percentile": 85.0,
            "last_seen": "2026-02-05",
            "trend": "up",
            "trend_delta": 12
        }
    },
    
    "characters": {
        "రాము": {
            "count": 1021,
            "document_frequency": 950,
            "tfidf_score": 0.38,
            "rank": 1,
            "co_occurs_with": ["సీత", "లక్ష్మణుడు", "హనుమంతుడు"]
        }
    },
    
    "locations": {
        "అడవి": {
            "count": 890,
            "document_frequency": 750,
            "tfidf_score": 0.42,
            "rank": 1,
            "co_occurs_with": ["జంతువులు", "వేటగాడు", "రాజు"]
        }
    },
    
    "genres": {
        "FOLKLORE": {
            "count": 3500,
            "percentage": 34.3
        },
        "MORAL_STORY": {
            "count": 2800,
            "percentage": 27.4
        }
    },
    
    "authors": {
        "చందమామ బృందం": {
            "count": 5115,
            "percentage": 50.1
        }
    },
    
    "temporal": {
        "by_decade": {
            "1940s": 200,
            "1950s": 1500,
            "1960s": 2000,
            "1970s": 2500,
            "1980s": 2000,
            "1990s": 1500,
            "2000s": 500,
            "2010s": 12
        },
        "by_year": {
            "1947": 50,
            "1948": 120
        }
    },
    
    "co_occurrence_matrix": {
        "keywords": {
            "రాజు": ["మంత్రి", "రాజ్యం", "గర్వం", "వినయం"],
            "అడవి": ["జంతువులు", "వేడి", "రాజు", "అమ్మాయి"]
        }
    },
    
    "trending": {
        "rising": [
            {"keyword": "మాయ", "delta": 15},
            {"keyword": "సాహసం", "delta": 12}
        ],
        "falling": [
            {"keyword": "పురాణం", "delta": -5}
        ]
    }
}
```

---

## Field Definitions

### Corpus Stats

| Field | Type | Description |
|-------|------|-------------|
| `total_stories` | int | Total number of stories in archive |
| `total_words` | int | Total word count across all stories |
| `total_unique_keywords` | int | Distinct keywords in corpus |

### Keyword Entry

| Field | Type | Description |
|-------|------|-------------|
| `count` | int | Raw occurrence count |
| `document_frequency` | int | Number of stories containing this keyword |
| `tfidf_score` | float | TF-IDF score (0-1, higher = more distinctive) |
| `rank` | int | Position in sorted list (1 = most frequent) |
| `percentile` | float | Percentile ranking (99 = top 1%) |
| `last_seen` | date | Last story date containing this keyword |
| `trend` | enum | `up`, `down`, `stable` |
| `trend_delta` | int | Rank change in last 30 days |

### Trend Calculation

```python
trend = "stable"
if rank_30_days_ago - current_rank > 10:
    trend = "up"
elif current_rank - rank_30_days_ago > 10:
    trend = "down"
```

---

## TF-IDF Calculation

```python
import math

def calculate_tfidf(keyword: str, stats: dict) -> float:
    """
    Calculate TF-IDF score for a keyword.
    
    TF = keyword_count / total_keywords_in_corpus
    IDF = log(total_stories / document_frequency)
    """
    total_stories = stats["corpus_stats"]["total_stories"]
    total_words = stats["corpus_stats"]["total_words"]
    
    kw_stats = stats["keywords"][keyword]
    count = kw_stats["count"]
    doc_freq = kw_stats["document_frequency"]
    
    # Term Frequency (normalized)
    tf = count / total_words
    
    # Inverse Document Frequency
    idf = math.log(total_stories / max(doc_freq, 1))
    
    # TF-IDF score (scaled to 0-1)
    tfidf = tf * idf
    
    # Normalize to 0-1 range
    max_tfidf = 0.001  # Approximate max for normalization
    normalized = min(tfidf / max_tfidf, 1.0)
    
    return round(normalized, 4)
```

---

## Update Strategies

### Incremental Update (Every 15 minutes)

```python
def incremental_update(new_story_metadata: dict):
    """Fast update for new story ingestion."""
    
    stats = load_enhanced_stats()
    
    # Update counts
    for keyword in new_story_metadata["keywords"]:
        if keyword in stats["keywords"]:
            stats["keywords"][keyword]["count"] += 1
            stats["keywords"][keyword]["document_frequency"] += 1
            stats["keywords"][keyword]["last_seen"] = today()
        else:
            stats["keywords"][keyword] = {
                "count": 1,
                "document_frequency": 1,
                "tfidf_score": 0,  # Calculated in nightly
                "rank": len(stats["keywords"]) + 1,
                "last_seen": today(),
                "trend": "new"
            }
    
    stats["corpus_stats"]["total_stories"] += 1
    stats["last_incremental_update"] = now()
    
    save_enhanced_stats(stats)
```

### Nightly Full Recalculation (2 AM)

```python
def nightly_full_recalculation():
    """Complete recalculation of all rankings and scores."""
    
    stats = load_enhanced_stats()
    
    # 1. Recalculate all TF-IDF scores
    for keyword in stats["keywords"]:
        stats["keywords"][keyword]["tfidf_score"] = \
            calculate_tfidf(keyword, stats)
    
    # 2. Re-rank by TF-IDF score (descending)
    sorted_keywords = sorted(
        stats["keywords"].items(),
        key=lambda x: x[1]["tfidf_score"],
        reverse=True
    )
    
    for rank, (keyword, data) in enumerate(sorted_keywords, 1):
        old_rank = data.get("rank", rank)
        data["rank"] = rank
        data["percentile"] = (1 - rank/len(sorted_keywords)) * 100
        
        # Calculate trend
        delta = old_rank - rank
        data["trend_delta"] = delta
        if delta > 10:
            data["trend"] = "up"
        elif delta < -10:
            data["trend"] = "down"
        else:
            data["trend"] = "stable"
    
    # 3. Rebuild co-occurrence matrix
    stats["co_occurrence_matrix"] = build_co_occurrence()
    
    # 4. Calculate trending keywords
    stats["trending"] = calculate_trending(stats)
    
    stats["generated_at"] = now()
    save_enhanced_stats(stats)
```

---

## Migration from global_stats.json

```python
def migrate_legacy_stats():
    """One-time migration from old format."""
    
    with open("data/stats/global_stats.json") as f:
        old = json.load(f)
    
    enhanced = {
        "version": "2.0",
        "generated_at": now(),
        "corpus_stats": {
            "total_stories": old["total_stories"],
            "total_words": estimate_word_count(),
            "total_unique_keywords": len(old.get("keywords", {}))
        },
        "keywords": {},
        "characters": {},
        "locations": {},
        "genres": {},
        "authors": {}
    }
    
    # Convert keywords
    for keyword, count in old.get("keywords", {}).items():
        enhanced["keywords"][keyword] = {
            "count": count,
            "document_frequency": count,  # Approximate
            "tfidf_score": 0,  # Will be calculated
            "rank": 0,
            "last_seen": "unknown",
            "trend": "stable"
        }
    
    # Similar for characters, locations...
    
    # Calculate TF-IDF scores
    nightly_full_recalculation()
    
    return enhanced
```

---

## Backward Compatibility

The enhanced stats file lives alongside the existing `global_stats.json`:

```
data/stats/
├── global_stats.json       # Legacy (kept for backward compat)
└── enhanced_stats.json     # New (used by agents)
```

Existing UI components can continue using `global_stats.json` while new features use `enhanced_stats.json`.
