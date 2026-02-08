# Master Architecture & Flow Diagrams

> **Visual reference for the complete Telugu Agentic RAG System**

This document provides high-fidelity diagrams for the entire system, connecting Ingestion (Workflow 1) and Generation (Workflow 2).

---

## 1. Unified System Architecture

This diagram shows how both workflows connect through the shared storage layer.

```mermaid
graph TB
    subgraph "External World"
        USER(("User / Admin"))
    end

    subgraph "Workflow 1: Ingestion & Knowledge Building"
        direction TB
        UI_INGEST["Ingestion UI"]

        subgraph "Ingestion Agents"
            V_AGENT["🛡️ Story Validation Agent"]
            M_AGENT["📊 Metadata Agent"]
            I_AGENT["💾 Ingestion Agent"]
            K_AGENT["📈 Keyword Agent (Async)"]
        end

        UI_INGEST -->|Raw Text| V_AGENT
        V_AGENT -->|Validated Text| M_AGENT
        M_AGENT -->|Full Metadata| I_AGENT
        I_AGENT -->|Events| K_AGENT
    end

    subgraph "Storage Layer"
        QDRANT[("Qdrant Cloud<br/>(Vectors + Metadata)")]
        SUPABASE[("Supabase<br/>(Backup & Stats)")]
        LOCAL_FS[("File System<br/>(Logs & Backups)")]
    end

    subgraph "Workflow 2: Story Generation"
        direction TB
        UI_GEN["Geneartion UI"]

        subgraph "Generation Agents"
            P_AGENT["✨ Prompt Agent"]
            M_AGENT_GEN["📊 Metadata Agent (Reusable)"]
            RAG_AGENT["🧠 RAG Agent"]
            VAL_AGENT["✅ Validator Agent"]
        end

        UI_GEN -->|User Prompt| P_AGENT
        P_AGENT -->|Telugu Prompt| M_AGENT_GEN
        M_AGENT_GEN -->|Search Metadata| RAG_AGENT
        RAG_AGENT -->|Draft Story| VAL_AGENT
        VAL_AGENT -->|Final Story| UI_GEN
    end

    %% Connections to Storage
    I_AGENT ==> QDRANT
    I_AGENT -.-> SUPABASE
    K_AGENT -.-> SUPABASE

    QDRANT <==>|Context Retrieval| RAG_AGENT

    %% Legend
    style USER fill:#fff,stroke:#333,stroke-width:2px
    style QDRANT fill:#d1c4e9,stroke:#512da8,stroke-width:2px
    style SUPABASE fill:#c5cae9,stroke:#303f9f,stroke-width:2px

    classDef ingest fill:#e8f5e9,stroke:#2e7d32
    classDef gen fill:#fff3e0,stroke:#e65100

    class V_AGENT,M_AGENT,I_AGENT,K_AGENT ingest
    class P_AGENT,M_AGENT_GEN,RAG_AGENT,VAL_AGENT gen
```

---

## 2. Ingestion Data Pipeline (Data Transformation)

Shows how data transforms from raw text to a vector point.

```mermaid
classDiagram
    direction LR

    class RawInput {
        +String text
        +Object user_fields
        +String status="Unverified"
    }

    class ValidatedObject {
         +String text
         +Boolean valid=true
         +Float telugu_ratio
         +List checks_passed
    }

    class EnrichedMetadata {
         +String text
         +List keywords
         +String genre
         +String theme
         +String summary
         +Int year
         +Int month
    }

    class VectorEntry {
         +UUID id
         +Vector embedding (768d)
         +Object payload
    }

    RawInput --> ValidatedObject : Story Validation Agent
    ValidatedObject --> EnrichedMetadata : Metadata Generation Agent
    EnrichedMetadata --> VectorEntry : Ingestion Agent
```

---

## 3. Story Generation State Machine

Shows the lifecycle of a story request, including the regeneration loop.

```mermaid
stateDiagram-v2
    [*] --> Prompting

    state Prompting {
        [*] --> RawPrompt
        RawPrompt --> Translated : Prompt Agent
        Translated --> Optimized : Prompt Agent
    }

    Optimized --> Retrieving : Handover to RAG

    state Retrieving {
        [*] --> Querying
        Querying --> ContextFound : Qdrant Search
    }

    ContextFound --> Generating : Handover to LLM

    state Generating {
        [*] --> Drafting
        Drafting --> DraftComplete : Stream Finish
    }

    DraftComplete --> Validating : Handover to Validator

    state Validating {
        [*] --> Evaluating
        Evaluating --> QualityCheck

        state QualityCheck <<choice>>
        QualityCheck --> Polishing : Score >= 6.0
        QualityCheck --> Failed : Score < 6.0

        Polishing --> Approved : Grammar Fixes
    }

    Approved --> [*] : Return to User

    state Failed {
        [*] --> CheckRetries

        state CheckRetries <<choice>>
        CheckRetries --> Regenerating : Attempt < 3
        CheckRetries --> ForceApprove : Attempt >= 3
    }

    Regenerating --> Generating : New Instructions
    ForceApprove --> [*] : Return with Warning
```

---

## 4. Agent Decision Gates

Visualizing the "Brain" of the system: where decisions are made.

```mermaid
flowchart TD
    subgraph Gate_1_Ingestion [Gate 1: Ingestion Validation]
        A[Script Checks] -->|Fail| R1[Reject]
        A -->|Pass| B[LLM Checks]
        B -->|Fail| R1
        B -->|Pass| P1{Next Step}
    end

    subgraph Gate_2_Optimization [Gate 2: Prompt Optimization]
        C[Language Check] -->|Telugu| D[Expand Only]
        C -->|Other| E[Translate + Expand]
        D --> F[Facet Integration]
        E --> F
    end

    subgraph Gate_3_Quality [Gate 3: Quality Assurance]
        G[Evaluate Score] -->|Score < 6| H[Feedback Gen]
        G -->|6 <= Score < 8| I[Polish Required]
        G -->|Score >= 8| J[Perfect Pass]

        H --> K{Retry Count < 3?}
        K -->|Yes| L[Regenerate]
        K -->|No| I
    end

    P1 ==> Gate_2_Optimization
    F ==> Gate_3_Quality
```
