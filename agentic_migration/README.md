# Agentic Architecture Migration Package

> **Self-contained documentation for transitioning Chandamama Studio to a multi-agent architecture**

---

## Quick Start

1. Copy this entire `agentic_migration/` directory to your new repository
2. Read `architecture/overview.md` first
3. Review agent specs in `agents/`
4. Follow migration phases in `architecture/migration_plan.md`

---

## Directory Structure

```
agentic_migration/
├── README.md                      # This file
├── architecture/
│   ├── overview.md                # High-level architecture & system diagram
│   ├── understanding_confirmation.md  # Analysis of existing system
│   ├── workflow_1_ingestion.md    # Story ingestion pipeline
│   ├── workflow_2_generation.md   # Story generation pipeline
│   └── migration_plan.md          # Phased rollout strategy
├── agents/
│   ├── story_validation_agent.md  # Telugu content validation
│   ├── metadata_generation_agent.md  # Auto-extract metadata
│   ├── ingestion_vectorization_agent.md  # Qdrant storage
│   ├── prompt_improvisation_agent.md  # Prompt enhancement
│   ├── rag_agent.md               # Retrieval + generation
│   ├── validator_improvisor_agent.md  # Quality gating
│   └── keyword_intelligence_agent.md  # TF-IDF ranking & stats
└── schemas/
    └── enhanced_stats_schema.md   # New stats format with TF-IDF
```

---

## Architecture Summary

### Two Workflows

| Workflow | Purpose | Agents |
|----------|---------|--------|
| **WF1: Ingestion** | Validate, extract metadata, store stories | Validation → Metadata → Ingestion → Keyword |
| **WF2: Generation** | Generate quality-validated Telugu stories | Prompt → Metadata → RAG → Validator |

### Storage Model

| Storage | Role | Sync |
|---------|------|------|
| **Qdrant Cloud** | Primary (vectors + metadata + text) | Real-time |
| **Local Disk** | Snapshot backup | Weekly |
| **Supabase** | Durable backup | Weekly |

### Key Design Decisions

1. **TF-IDF Ranking** - Keywords ranked by distinctiveness, not just frequency
2. **Incremental + Nightly** - Fast updates + heavy compute batched
3. **Two-Step Validation** - Script-first, LLM-second to reduce costs
4. **Feature Flags** - Every agent toggleable for safe rollout

---

## Reading Order

1. **Start here**: `architecture/understanding_confirmation.md`
2. **Architecture**: `architecture/overview.md`
3. **Workflows**: `workflow_1_ingestion.md`, `workflow_2_generation.md`
4. **Agent details**: Browse `agents/` as needed
5. **Migration**: `architecture/migration_plan.md`

---

## Agent Summary

| Agent | LLM? | Purpose |
|-------|------|---------|
| Story Validation | ✅ (conditional) | Reject invalid Telugu content |
| Metadata Generation | ✅ (conditional) | Extract keywords, genre, theme |
| Ingestion & Vectorization | ❌ | Store to Qdrant |
| Keyword Intelligence | ❌ | TF-IDF ranking, trend tracking |
| Prompt Improvisation | ✅ | Translate & enhance prompts |
| RAG Agent | ✅ | Retrieve context + generate |
| Validator & Improvisor | ✅ | Quality gate + polish |

---

## New Stats Format

See `schemas/enhanced_stats_schema.md` for the new `enhanced_stats.json` format:

```json
{
    "keywords": {
        "రాజు": {
            "count": 1021,
            "tfidf_score": 0.45,
            "rank": 1,
            "trend": "stable"
        }
    }
}
```

---

## Migration Phases

1. **Phase 0**: Feature flags, base agent class
2. **Phase 1**: Prompt Improvisation Agent
3. **Phase 2**: Story Validation Agent
4. **Phase 3**: Metadata Generation Agent
5. **Phase 4**: Validator & Improvisor Agent
6. **Phase 5**: Full integration, cleanup

Each phase is independently rollback-able via feature flags.

---

## Dependencies (When Implementing)

```python
# requirements.txt additions
sentence-transformers>=2.2.0
qdrant-client>=1.7.0
supabase>=2.0.0  # For backup only
```

---

## Questions?

Refer to `architecture/understanding_confirmation.md` for analysis of the existing system, or the individual agent specs for implementation details.
