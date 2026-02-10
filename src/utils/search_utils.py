from collections import defaultdict
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

def group_results_by_story(
    scored_points: List[Any],
    max_stories: int = 10,
    max_chunks_per_story: int = 4
) -> List[Dict[str, Any]]:
    """
    Groups Qdrant search results strictly by story_id with Stage 3 Polish.

    Rules:
    1. Group by story_id.
    2. Sort chunks by chunk_index (reading order).
    3. Rank stories by best chunk score (descending).
    4. Limit: Top 10 stories.
    5. Limit: Max 4 chunks per story.
    6. Labels: Content Type & Scope ([FULL STORY] vs [MATCHING CHUNKS]).

    Args:
        scored_points: List of ScoredPoint objects.
        max_stories: Limit number of stories returned (default 10).
        max_chunks_per_story: Limit chunks per story (default 4).

    Returns:
        Sorted list of story dictionaries.
    """
    stories = defaultdict(list)
    seen_chunks = set()

    # 1. Group by story_id
    for p in scored_points:
        payload = p.payload
        chunk_id = payload.get("chunk_id")

        if chunk_id in seen_chunks:
            continue
        seen_chunks.add(chunk_id)

        try:
            c_idx = int(payload.get("chunk_index", 0))
        except:
            c_idx = 0

        stories[payload["story_id"]].append({
            "chunk_id": chunk_id,
            "chunk_index": c_idx,
            "text": payload.get("text", ""),
            "score": p.score,
            "title": payload.get("title", "Unknown"),
            "year": payload.get("year"),
            "month": payload.get("month"),
            "content_type": payload.get("content_type", "STORY").upper(),
            "story_id": payload["story_id"]
        })

    grouped_list = []

    # 2. Process each story
    for story_id, chunks in stories.items():
        if not chunks:
            continue

        # A. Determine Best Score
        # Sort by score DESC to find best_score
        chunks.sort(key=lambda c: c["score"], reverse=True)
        best_score = chunks[0]["score"]

        # B. Metadata Aggregation
        # Find best available title (robustness)
        titles = [c["title"] for c in chunks if c["title"] and c["title"] != "Unknown"]
        best_title = titles[0] if titles else chunks[0]["title"]
        content_type = chunks[0]["content_type"] # Use type from highly ranked chunk

        # Metadata from a representative chunk
        year = chunks[0]["year"]
        month = chunks[0]["month"]

        # C. Sort Chunks by Index (Reading Order)
        chunks.sort(key=lambda c: c["chunk_index"])

        # D. Determine Scope Label check BEFORE slicing
        # Rule: "If a story has 2 or more sequential chunks starting from the beginning"
        # i.e., indices start at 1 and are sequential (1, 2...)
        scope_label = "[MATCHING CHUNKS ONLY]"
        if len(chunks) >= 2:
            indices = [c["chunk_index"] for c in chunks]
            # Check if it starts with 1 and includes 2 (basic sequential start)
            if indices[0] == 1 and indices[1] == 2:
                scope_label = "[FULL STORY]"

        # E. Enforce Chunk Limit
        final_chunks = chunks[:max_chunks_per_story]

        grouped_list.append({
            "story_id": story_id,
            "title": best_title,
            "year": year,
            "month": month,
            "content_type": content_type,
            "best_score": best_score,
            "scope_label": scope_label,
            "chunks": final_chunks
        })

    # 3. Sort Stories Globally by Best Score (Descending)
    grouped_list.sort(key=lambda s: s["best_score"], reverse=True)

    # 4. Enforce Story Limit
    return grouped_list[:max_stories]


def hydrate_stories(client: QdrantClient, collection_name: str, grouped_stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fetches ALL chunks for the provided stories to ensure no gaps in the narrative.

    Args:
        client: QdrantClient instance.
        collection_name: Name of the collection.
        grouped_stories: List of grouped story dictionaries.

    Returns:
        The same list of stories, but with 'chunks' populated by ALL chunks from the DB.
    """
    hydrated_stories = []

    for story in grouped_stories:
        story_id = story["story_id"]

        # Create filter for this specific story ID
        story_filter = Filter(
            must=[
                FieldCondition(
                    key="story_id",
                    match=MatchValue(value=story_id)
                )
            ]
        )

        # Scroll to get all chunks (handling pagination if necessary, though stories are usually small enough)
        # Using a large limit (e.g., 100) assuming stories don't exceed that many chunks.
        # If they do, we'd need a loop, but 100 * 500 tokens is a huge story.
        all_points, _ = client.scroll(
            collection_name=collection_name,
            scroll_filter=story_filter,
            limit=1000,
            with_payload=True
        )

        # Re-construct chunks list with full data
        all_chunks = []
        for p in all_points:
            payload = p.payload
            # Try to preserve the original relevance score if this chunk was in the initial search
            # Otherwise, it's a context chunk, so score is N/A (or 0)
            original_match = next((c for c in story["chunks"] if c["chunk_id"] == payload["chunk_id"]), None)
            score = original_match["score"] if original_match else 0.0

            # Robustness: Ensure chunk_index is int
            try:
                c_idx = int(payload.get("chunk_index", 0))
            except:
                c_idx = 0

            all_chunks.append({
                "chunk_id": payload["chunk_id"],
                "chunk_index": c_idx,
                "text": payload.get("text", ""),
                "score": score, # 0.0 indicates it was fetched for context, not relevance
                "content_type": payload.get("content_type", "STORY").upper(),
                "is_context": original_match is None # Flag to distinguish search hits from context
            })

        # Sort by index
        all_chunks.sort(key=lambda c: c["chunk_index"])

        # Update the story object
        story["chunks"] = all_chunks

        # Since we hydrated it, we have the full story
        story["scope_label"] = "[FULL STORY]"

        # Update content_type from the first chunk (as it might be more reliable now that we have all)
        if all_chunks:
             story["content_type"] = all_chunks[0]["content_type"]

        hydrated_stories.append(story)

    return hydrated_stories
