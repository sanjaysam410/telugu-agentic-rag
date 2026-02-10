# Telugu Agentic RAG System (AI Storyteller)

An advanced **Multi-Agent AI System** designed to generate high-quality, culturally nuanced Telugu stories. Unlike traditional "Monolithic" LLM scripts, this system employs a team of specialized agents to plan, draft, validate, and polish stories, ensuring they meet rigorous literary standards.

---

## 🚀 Why "Agentic" RAG? (vs. Old Monolithic Approach)

The transition from **Chandamama Studio (Monolithic)** to **Agentic RAG** represents a paradigm shift in AI storytelling.

| Feature | 🏛️ Old Monolithic Approach | 🤖 New Agentic Approach |
| :--- | :--- | :--- |
| **Process** | **Linear**: Input -> LLM -> Output. If it fails, it fails. | **Iterative**: Input -> Plan -> Draft -> **Critique** -> **Fix** -> Output. |
| **Quality Control** | **None**: You get what the LLM gives you. "Hallucinations" are common. | **Validator Agent**: A dedicated "Editor" agent reviews the story against 8 stringent rules and *rejects* or *fixes* it before you see it. |
| **Context** | **Static**: Uses a fixed prompt template for all stories. | **Dynamic RAG**: Searches a Vector Database for specific stylistic examples relevant to your request. |
| **Creativity** | **Robotic**: Often translates English thoughts to Telugu, sounding "bookish". | **"Think in Telugu"**: Enforces native thinking and idiom usage via the "8 Commandments". |
| **Architecture** | **Single Point of Failure**: One big script. | **Resilient**: If one agent fails (e.g., API error), others can retry or adapt. |

---

## 🛡️ The "8 Commandments" of Quality

This system doesn't just "write stories"; it adheres to a strict literary code enforced by the **Validator Agent**:

1.  **Show, Don't Tell**: Characters are introduced via **ACTION**, not trait dumping (e.g., *No "Raju is greedy". Show Raju snatching a coin.*).
2.  **Gradual Arcs**: Character transformation must follow a 4-stage path (Resistance -> Doubt -> Change -> Growth).
3.  **No Preaching**: "Double Morals" are banned. The story *is* the lesson; characters do not lecture.
4.  **Logical Consequences**: No "magical" fixes. Actions have real weight.
5.  **Object Permanence**: Items introduced must remain consistent in physics and utility.
6.  **Varied Sentence Structure**: No repetitive "Name... Name..." sentence starts.
7.  **Functional Description**: Atmosphere must serve the plot, not just decorate.
8.  **Earned Resolution**: Endings must be a result of character choice, not luck.

---

## 🧩 The Agent Team

1.  **Ingestion Agent**: Reads raw Telugu stories, cleans them, extracts metadata, and stores them in **Qdrant** (Vector DB).
2.  **Prompt Optimizer Agent**: "Thinks" about your request and expands it into a detailed blueprint before writing starts.
3.  **RAG Generator Agent (The Storyteller)**: Retrieves similar stories for style reference and drafts the narrative using the "Think in Telugu" safeguards.
4.  **Validator Agent (The Editor)**: The harshest critic. It reads the draft, checks the 8 Commandments, and auto-corrects minor issues or rejects major failures.

---


---

## 🏗️ Architecture

```mermaid
graph TD
    subgraph INGESTION[Workflow 1: Story Ingestion]
        Raw(Raw Text) -->|Validates| IV[Ingestion Validator]
        IV -->|Extracts Metadata| MD[Metadata Agent]
        MD -->|Embeds & Stores| Q[(Qdrant Vector DB)]
    end

    subgraph GENERATION[Workflow 2: Story Generation]
        User(User Request) -->|Refines| PO[Prompt Optimizer Agent]
        PO -->|Retrieves Style| RAG[RAG Retriever]
        RAG -.->|Queries| Q
        RAG -->|Drafts Story| GEN[Generator Agent]
        GEN -->|Critiques against 8-Points| VAL[Validator Agent]
        VAL -- REJECT / FIX --> GEN
        VAL -- ACCEPT --> Final(Final Story)
    end
```

---

## 🛠️ Installation & Setup

### 1. Requirements

- Python 3.10+
- **Google Gemini API Key** (or OpenAI/Groq)

### 2. Quick Start (Streamlit Cloud Ready)

This project uses a simple `requirements.txt` structure for easy deployment.

```bash
# Clone the repository
git clone <repo-url>
cd telugu-agentic-rag

# Setup Environment
cp .env.example .env
# Open .env and add your GOOGLE_API_KEY

# Install Dependencies
pip install -r requirements.txt

# Run the App
streamlit run app.py
```

### 3. Folder Structure

- `src/agents/`: The brains of the operation (Ingestion, Generation, Validation).
- `src/utils/`: Helper functions and the core `generation_utils.py` (Prompt Templates).
- `data/`: Local storage for vector chunks (excluded from git).
- `app.py`: The Main Interface.

---

## 🤝 Contributing

We welcome contributions regarding **Prompt Engineering** and **Dataset Expansion**.
See `CONTRIBUTING.md` for details.

---

**License**: AGPL-3.0
