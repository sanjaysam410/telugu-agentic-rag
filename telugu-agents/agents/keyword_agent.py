import json
import math
import os
import threading
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KeywordAgentConfig:
    """Configuration for Keyword Intelligence Agent"""
    
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


class KeywordAgent:
    """
    Keyword Intelligence Agent with TF-IDF scoring and incremental updates.
    
    Features:
    - Real-time in-memory updates on story ingestion
    - Incremental persistence every 15 minutes
    - Nightly full TF-IDF recalculation and ranking
    - Trend tracking with 30-day delta
    - Co-occurrence matrix generation
    """
    
    def __init__(self, config: KeywordAgentConfig = KeywordAgentConfig()):
        self.config = config
        
        # Thread-safe dirty tracking
        self._lock = threading.Lock()
        self._dirty_keywords = set()
        self._pending_updates = defaultdict(lambda: {"count": 0, "doc_freq": 0})
        
        # Ensure stats directory exists
        Path(config.STATS_FILE).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize stats if not exists
        if not os.path.exists(config.STATS_FILE):
            self._initialize_stats()
    
    def _initialize_stats(self):
        """Initialize empty stats structure"""
        stats = {
            "corpus_stats": {
                "total_stories": 0,
                "total_words": 0,
                "total_keywords": 0,
                "total_characters": 0,
                "total_locations": 0
            },
            "keywords": {},
            "characters": {},
            "locations": {},
            "authors": {},
            "genres": {},
            "co_occurrence_matrix": {"keywords": {}},
            "trending": {
                "rising": [],
                "falling": []
            },
            "last_incremental_update": None,
            "generated_at": datetime.now().isoformat()
        }
        self._save_enhanced_stats(stats)
        logger.info("Initialized empty stats structure")
    
    def _load_enhanced_stats(self) -> Dict[str, Any]:
        """Load enhanced stats from JSON"""
        try:
            with open(self.config.STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Stats file not found, initializing...")
            self._initialize_stats()
            return self._load_enhanced_stats()
        except json.JSONDecodeError as e:
            logger.error(f"Corrupt stats file: {e}")
            raise
    
    def _save_enhanced_stats(self, stats: Dict[str, Any]):
        """Save enhanced stats to JSON"""
        with open(self.config.STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    
    def calculate_tfidf(self, keyword: str, stats: Dict[str, Any]) -> float:
        """
        Calculate TF-IDF score for a keyword.
        
        Returns: float between 0-1 (higher = more distinctive)
        """
        corpus = stats["corpus_stats"]
        
        if keyword not in stats["keywords"]:
            return 0.0
        
        kw = stats["keywords"][keyword]
        
        # Avoid division by zero
        if corpus["total_words"] == 0 or corpus["total_stories"] == 0:
            return 0.0
        
        # Term Frequency (normalized by corpus size)
        tf = kw["count"] / corpus["total_words"]
        
        # Inverse Document Frequency
        # Add 1 to avoid division by zero
        idf = math.log(corpus["total_stories"] / max(kw["document_frequency"], 1))
        
        # Raw TF-IDF
        raw_tfidf = tf * idf
        
        # Normalize to 0-1 range (empirical max ~0.001)
        normalized = min(raw_tfidf / self.config.TFIDF_NORMALIZATION_FACTOR, 1.0)
        
        return round(normalized, 4)
    
    def on_story_ingested(self, metadata: Dict[str, Any]):
        """
        Called immediately after story ingestion. Non-blocking.
        
        Args:
            metadata: Story metadata containing keywords, characters, locations, etc.
        """
        keywords = metadata.get("keywords", [])
        characters = metadata.get("characters", [])
        locations = metadata.get("locations", [])
        author = metadata.get("author", "Unknown")
        genre = metadata.get("normalized_genre_code", "UNKNOWN")
        
        # Estimate word count (simple heuristic)
        word_count = len(keywords) * 10  # Rough estimate
        
        with self._lock:
            # Update keywords
            for keyword in keywords:
                self._pending_updates[("keyword", keyword)]["count"] += 1
                self._pending_updates[("keyword", keyword)]["doc_freq"] += 1
                self._dirty_keywords.add(("keyword", keyword))
            
            # Update characters
            for character in characters:
                self._pending_updates[("character", character)]["count"] += 1
                self._pending_updates[("character", character)]["doc_freq"] += 1
                self._dirty_keywords.add(("character", character))
            
            # Update locations
            for location in locations:
                self._pending_updates[("location", location)]["count"] += 1
                self._pending_updates[("location", location)]["doc_freq"] += 1
                self._dirty_keywords.add(("location", location))
            
            # Update authors
            self._pending_updates[("author", author)]["count"] += 1
            self._dirty_keywords.add(("author", author))
            
            # Update genres
            self._pending_updates[("genre", genre)]["count"] += 1
            self._dirty_keywords.add(("genre", genre))
            
            # Track corpus stats
            self._pending_updates[("corpus", "stories")]["count"] += 1
            self._pending_updates[("corpus", "words")]["count"] += word_count
        
        logger.info(f"Story ingested: {len(keywords)} keywords, {len(characters)} characters")
    
    def incremental_update(self):
        """
        Persist pending updates. Runs every 15 minutes.
        """
        with self._lock:
            if not self._dirty_keywords:
                logger.info("No dirty keywords, skipping incremental update")
                return  # Nothing to update
            
            dirty = self._dirty_keywords.copy()
            updates = dict(self._pending_updates)
            self._dirty_keywords.clear()
            self._pending_updates.clear()
        
        # Load current stats
        stats = self._load_enhanced_stats()
        
        # Apply updates
        for (entity_type, entity_name), delta in updates.items():
            if entity_type == "corpus":
                if entity_name == "stories":
                    stats["corpus_stats"]["total_stories"] += delta["count"]
                elif entity_name == "words":
                    stats["corpus_stats"]["total_words"] += delta["count"]
                continue
            
            # Determine target dict
            if entity_type == "keyword":
                target = stats["keywords"]
                stats["corpus_stats"]["total_keywords"] += delta["count"]
            elif entity_type == "character":
                target = stats["characters"]
                stats["corpus_stats"]["total_characters"] += delta["count"]
            elif entity_type == "location":
                target = stats["locations"]
                stats["corpus_stats"]["total_locations"] += delta["count"]
            elif entity_type == "author":
                target = stats["authors"]
            elif entity_type == "genre":
                target = stats["genres"]
            else:
                continue
            
            # Initialize if new
            if entity_name not in target:
                target[entity_name] = {
                    "count": 0,
                    "document_frequency": 0,
                    "tfidf_score": 0,
                    "rank": len(target) + 1,
                    "percentile": 0,
                    "last_seen": datetime.now().isoformat(),
                    "trend": "new",
                    "trend_delta": 0
                }
            
            # Update counts
            target[entity_name]["count"] += delta["count"]
            if "doc_freq" in delta:
                target[entity_name]["document_frequency"] += delta["doc_freq"]
            target[entity_name]["last_seen"] = datetime.now().isoformat()
        
        # Update timestamp
        stats["last_incremental_update"] = datetime.now().isoformat()
        
        # Save
        self._save_enhanced_stats(stats)
        logger.info(f"Incremental update: {len(dirty)} entities updated")
        
        # Sync legacy stats
        self.sync_legacy_stats()
    
    def nightly_full_recalculation(self):
        """
        Complete recalculation. Runs at 2 AM daily.
        """
        logger.info("Starting nightly full recalculation...")
        stats = self._load_enhanced_stats()
        
        # 1. Recalculate ALL TF-IDF scores for keywords
        for keyword in stats["keywords"]:
            stats["keywords"][keyword]["tfidf_score"] = \
                self.calculate_tfidf(keyword, stats)
        
        # 2. Sort and rank by TF-IDF (descending)
        sorted_keywords = sorted(
            stats["keywords"].items(),
            key=lambda x: x[1]["tfidf_score"],
            reverse=True
        )[:self.config.MAX_KEYWORDS_TO_RANK]
        
        total = len(sorted_keywords)
        for rank, (keyword, data) in enumerate(sorted_keywords, 1):
            old_rank = data.get("rank", rank)
            
            data["rank"] = rank
            data["percentile"] = round((1 - rank/total) * 100, 1) if total > 0 else 0
            
            # Calculate trend (30-day window)
            delta = old_rank - rank
            data["trend_delta"] = delta
            
            if delta > self.config.TREND_THRESHOLD:
                data["trend"] = "up"
            elif delta < -self.config.TREND_THRESHOLD:
                data["trend"] = "down"
            else:
                data["trend"] = "stable"
        
        # 3. Rebuild co-occurrence matrix
        # Note: This requires access to Qdrant, so we'll create a placeholder
        stats["co_occurrence_matrix"] = self.build_co_occurrence_matrix(stats)
        
        # 4. Generate trending lists
        rising = sorted(
            [(k, d["trend_delta"]) for k, d in stats["keywords"].items()
             if d["trend_delta"] > self.config.TREND_THRESHOLD],
            key=lambda x: x[1],
            reverse=True
        )[:self.config.TOP_TRENDING_COUNT]
        
        falling = sorted(
            [(k, d["trend_delta"]) for k, d in stats["keywords"].items()
             if d["trend_delta"] < -self.config.TREND_THRESHOLD],
            key=lambda x: x[1]
        )[:10]
        
        stats["trending"] = {
            "rising": [{"keyword": k, "delta": d} for k, d in rising],
            "falling": [{"keyword": k, "delta": d} for k, d in falling]
        }
        
        stats["generated_at"] = datetime.now().isoformat()
        self._save_enhanced_stats(stats)
        
        logger.info(f"Nightly recalc complete: {total} keywords ranked")
        
        # Sync legacy stats
        self.sync_legacy_stats()
    
    def build_co_occurrence_matrix(self, stats: Dict[str, Any], top_n: int = None) -> Dict[str, Any]:
        """
        Build keyword co-occurrence matrix.
        
        Note: This is a placeholder implementation. In production, this would
        scan all stories from Qdrant to find co-occurring keywords.
        """
        if top_n is None:
            top_n = self.config.MAX_CO_OCCURRENCE_KEYWORDS
        
        # Get top N keywords by frequency
        top_keywords = sorted(
            stats["keywords"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:top_n]
        
        # Placeholder: In production, scan Qdrant for actual co-occurrences
        matrix = {}
        for keyword, _ in top_keywords:
            # For now, just return empty lists
            # In production: query Qdrant for stories containing this keyword
            # and count co-occurring keywords
            matrix[keyword] = []
        
        return {"keywords": matrix}
    
    def sync_legacy_stats(self):
        """Keep legacy format in sync for backward compatibility."""
        enhanced = self._load_enhanced_stats()
        
        legacy = {
            "total_stories": enhanced["corpus_stats"]["total_stories"],
            "keywords": {k: d["count"] for k, d in enhanced["keywords"].items()},
            "characters": {k: d["count"] for k, d in enhanced["characters"].items()},
            "locations": {k: d["count"] for k, d in enhanced["locations"].items()},
            "authors": {k: d["count"] for k, d in enhanced["authors"].items()},
            "genres": {k: d["count"] for k, d in enhanced["genres"].items()},
            "generated_at": enhanced["generated_at"]
        }
        
        with open(self.config.LEGACY_STATS_FILE, "w", encoding='utf-8') as f:
            json.dump(legacy, f, ensure_ascii=False, indent=2)
        
        logger.info("Legacy stats synced")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current stats"""
        return self._load_enhanced_stats()
    
    def get_keyword_stats(self, keyword: str) -> Optional[Dict[str, Any]]:
        """Get stats for a specific keyword"""
        stats = self._load_enhanced_stats()
        return stats["keywords"].get(keyword)


if __name__ == "__main__":
    # Simple test
    agent = KeywordAgent()
    
    # Simulate story ingestion
    test_metadata = {
        "keywords": ["రాజు", "వినయం", "గర్వం"],
        "characters": ["రాజు", "మంత్రి"],
        "locations": ["రాజ్యం", "అడవి"],
        "normalized_genre_code": "MORAL_STORY",
        "author": "విశ్వం"
    }
    
    agent.on_story_ingested(test_metadata)
    agent.incremental_update()
    
    print("Stats after ingestion:")
    stats = agent.get_stats()
    
    # Write to file to avoid Windows console encoding issues
    with open("data/stats/test_output.json", "w", encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"Stats written to data/stats/test_output.json")
    print(f"Total keywords: {len(stats['keywords'])}")
    print(f"Total stories: {stats['corpus_stats']['total_stories']}")
