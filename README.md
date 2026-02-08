# Telugu Agentic RAG System

Multi-agent architecture for Telugu story generation using RAG (Retrieval-Augmented Generation).

## Features

- **Story Ingestion** - Validate, extract metadata, and vectorize Telugu stories
- **Story Generation** - Generate quality-validated Telugu stories with RAG
- **TF-IDF Keyword Ranking** - Smart keyword ranking with trend tracking
- **Quality Gating** - Automatic story validation with regeneration loop

## Quick Start

```bash
# Install dependencies
uv sync

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Run the application
uv run streamlit run app.py
```

## Architecture

See `agentic_migration/README.md` for full architecture documentation.

### Agents

| Agent | Purpose |
|-------|---------|
| Validation | Validate Telugu content |
| Metadata | Extract keywords, genre, theme |
| Ingestion | Store to Qdrant |
| Keyword | TF-IDF ranking & stats |
| Prompt | Enhance user prompts |
| RAG | Retrieve context + generate |
| Validator | Quality gate + polish |

## Development

```bash
# Format code
ruff format .

# Lint
ruff check .

# Run tests
uv run pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

AGPL-3.0
