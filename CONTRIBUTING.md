# Contributing to Telugu Agentic RAG System

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

---

## Getting Started

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- Qdrant Cloud account (or local Qdrant instance)
- Access to LLM API (Groq/OpenAI)

### Development Setup

```bash
# Clone the repository
git clone <repo-url>
cd telugu-agentic-rag

# Install dependencies
uv sync

# Copy environment template
cp .env.example .env

# Fill in your API keys
# QDRANT_URL=...
# QDRANT_API_KEY=...
# GROQ_API_KEY=...
```

---

## Project Structure

```
telugu-agentic-rag/
├── src/
│   ├── agents/           # Agent implementations
│   ├── retrieval/        # Vector search & RAG
│   ├── story_embedder/   # Embedding pipeline
│   └── config.py         # Configuration
├── data/
│   ├── chunks/           # Chunked stories
│   └── stats/            # Global statistics
├── docs/
│   ├── architecture/     # System design docs
│   └── agents/           # Agent specifications
└── tests/                # Unit & integration tests
```

---

## Code Style

### Python
- Follow [PEP 8](https://pep8.org/)
- Use [Ruff](https://github.com/astral-sh/ruff) for linting
- Type hints required for public functions
- Docstrings for all classes and public methods

```bash
# Format code
ruff format .

# Lint
ruff check .
```

### Markdown
- Use proper headings hierarchy
- Include code blocks with language specifiers
- Keep lines under 100 characters when possible

---

## Making Changes

### Branch Naming

```
feature/add-validation-agent
bugfix/fix-embedding-timeout
docs/update-architecture
refactor/simplify-rag-pipeline
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(agents): add story validation agent
fix(retrieval): handle empty query vectors
docs(architecture): update storage diagram
refactor(embedder): extract token counting logic
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear commits
3. Ensure tests pass: `uv run pytest`
4. Update documentation if needed
5. Submit PR with description of changes
6. Address review feedback

---

## Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_validation_agent.py

# Run with coverage
uv run pytest --cov=src
```

### Test Requirements

- All new agents must have unit tests
- Integration tests for workflow changes
- Mock LLM calls in unit tests (avoid API costs)

---

## Agent Development

When adding a new agent:

1. Create spec in `docs/agents/<agent_name>.md`
2. Implement in `src/agents/<agent_name>.py`
3. Add feature flag in `src/config.py`
4. Write tests in `tests/test_<agent_name>.py`
5. Update `docs/architecture/overview.md`

### Agent Template

```python
# src/agents/example_agent.py

from dataclasses import dataclass
from typing import Any

@dataclass
class ExampleAgentInput:
    text: str
    metadata: dict

@dataclass
class ExampleAgentOutput:
    result: str
    confidence: float

class ExampleAgent:
    """Brief description of what this agent does."""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
    
    def run(self, input: ExampleAgentInput) -> ExampleAgentOutput:
        """Process input and return output."""
        # Implementation
        pass
```

---

## Telugu Language Guidelines

- Use UTF-8 encoding for all Telugu text
- Test with actual Telugu content, not transliterated
- Validate Telugu script detection with `langdetect` or regex
- Keywords and metadata should preserve Telugu characters

---

## Questions?

- Check existing [issues](../../issues) for similar questions
- Open a new issue for bugs or feature requests
- Tag maintainers for urgent matters

---

## License

By contributing, you agree that your contributions will be licensed under the project's license.
