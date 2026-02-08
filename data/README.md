# Chandamama Archive Data (1947-2012)

## 🌙 Dataset Overview
This directory contains the digitized metadata and content of **Chandamama Magazine**, covering 66 years of publication history.

### 📂 Directory Structure
```text
data/
├── 1947-2012/           # Raw JSON Metadata (Organized by Year/Month)
│   ├── 1947/
│   │   └── చందమామ_1947_07.json
│   └── ...
├── chunks/              # Processed Text Chunks (for RAG/Search)
├── stats/               # Aggregated Statistics
│   ├── global_stats.json
│   └── poem_stats.json
└── qdrant_db/           # Vector Database (Embeddings) - (Usually External/Ignored)
```

## 📊 Content Insights (Snapshot)
From the scanned archive (`1947-2012`), we have indexed:
*   **Total Stories**: ~10,000+
*   **Unique Authors**: 2,500+
*   **Key Themes**: Moral (Neethi), Folklore (Janapadam), Mythology (Pouranikam)

## ✅ Coverage Status
*   **Total Years**: 1947-2012
*   **Coverage**: ~96% of all published months are indexed.
*   **Missing Data**: Small gaps exist in 1947, 1950, 1954, 1998, 1999 due to missed publication months or missing scans.

## 🛠 How to Use
1.  **Raw Data**: Access `1947-2012/` for full JSON files containing story text, authors, and metadata.
2.  **Analysis**: Use `stats/*.json` for quick aggregation of authors, genres, and keywords.
3.  **Search**: The `chunks/` directory contains pre-split text segments used by the application's retrieval system.
