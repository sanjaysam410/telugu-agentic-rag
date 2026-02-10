# Telugu Agents 🤖

A standalone package of intelligent agents for Telugu story processing and optimization.

## 📦 What's Included

This package contains two powerful agents:

### 1. **Keyword Agent** 📊
TF-IDF based keyword intelligence with real-time analytics and trend tracking.

**Features:**
- Real-time keyword tracking and TF-IDF scoring
- Trend analysis (rising/falling keywords)
- Co-occurrence matrix generation
- Character, location, and genre analytics
- Incremental updates every 15 minutes
- Nightly full recalculation

### 2. **Prompt Agent** ✍️
LLM-powered prompt optimization and translation for Telugu storytelling.

**Features:**
- Multi-language support (English, Telugu, Hindi, Tamil, Kannada, Malayalam)
- Automatic translation to natural Telugu
- Prompt expansion with narrative elements
- Facet integration (genre, tone, characters, locations)
- Intent preservation

## 🚀 Quick Start

### Installation

1. **Clone or copy this folder** to your project:
   ```bash
   cd your-project
   cp -r /path/to/telugu-agents .
   ```

2. **Install dependencies:**
   ```bash
   cd telugu-agents
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

### Running the Dashboards

#### Keyword Intelligence Dashboard
```bash
cd telugu-agents
streamlit run dashboards/keyword_dashboard.py
```

**Features:**
- 📈 Corpus overview with metrics
- 🏆 Top keywords by TF-IDF score
- 🔥 Trending keywords (rising/falling)
- 🔍 Keyword search
- 🔗 Co-occurrence analysis
- 📊 Genre and author analytics

#### Prompt Optimizer Dashboard
```bash
cd telugu-agents
streamlit run dashboards/prompt_optimizer.py
```

**Features:**
- ✍️ Multi-language input support
- 🎛️ Facet configuration (genre, tone, keywords, characters, locations)
- ✨ One-click prompt optimization
- 📜 Telugu output with full JSON details

## 💻 Usage Examples

### Keyword Agent

```python
from agents import KeywordAgent

# Initialize agent
agent = KeywordAgent()

# Simulate story ingestion
story_metadata = {
    "keywords": ["రాజు", "వినయం", "గర్వం"],
    "characters": ["రాజు", "మంత్రి"],
    "locations": ["రాజ్యం", "అడవి"],
    "normalized_genre_code": "MORAL_STORY",
    "author": "విశ్వం"
}

# Process story
agent.on_story_ingested(story_metadata)
agent.incremental_update()

# Get stats
stats = agent.get_stats()
print(f"Total keywords: {len(stats['keywords'])}")

# Get specific keyword stats
keyword_stats = agent.get_keyword_stats("రాజు")
print(f"TF-IDF Score: {keyword_stats['tfidf_score']}")
```

### Prompt Agent

```python
from agents import PromptAgent

# Initialize agent
agent = PromptAgent()

# Process prompt
result = agent.process_prompt(
    user_prompt="clever farmer",
    language="en",
    facets={
        "genre": "folk",
        "tone": "Traditional",
        "keywords": ["wisdom", "village"],
        "characters": ["farmer", "merchant"],
        "locations": ["village", "market"]
    }
)

# View result
print(f"Original: {result['original_prompt']}")
print(f"Telugu: {result['telugu_prompt']}")
print(f"Expansion applied: {result['expansion_applied']}")
```

## 📁 Package Structure

```
telugu-agents/
├── agents/                 # Core agent implementations
│   ├── __init__.py
│   ├── keyword_agent.py   # Keyword intelligence agent
│   └── prompt_agent.py    # Prompt optimization agent
├── utils/                  # Utility functions
│   ├── __init__.py
│   └── telugu_utils.py    # Telugu text processing utilities
├── dashboards/             # Streamlit dashboards
│   ├── keyword_dashboard.py
│   └── prompt_optimizer.py
├── data/                   # Data storage
│   └── stats/             # Keyword agent statistics
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── setup.py               # Package installation script
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```bash
# Required for Prompt Agent
GEMINI_API_KEY=your-gemini-api-key-here
```

### Keyword Agent Configuration

The Keyword Agent can be configured via `KeywordAgentConfig`:

```python
from agents import KeywordAgent, KeywordAgentConfig

config = KeywordAgentConfig()
config.INCREMENTAL_INTERVAL_MINUTES = 30  # Change update interval
config.TOP_TRENDING_COUNT = 50            # More trending keywords

agent = KeywordAgent(config)
```

### Prompt Agent Configuration

The Prompt Agent can be configured via `PromptAgentConfig`:

```python
from agents import PromptAgent, PromptAgentConfig

config = PromptAgentConfig()
config.MAX_RETRIES = 3                    # More retry attempts
config.MIN_TELUGU_RATIO = 0.7             # Stricter Telugu validation

agent = PromptAgent(config)
```

## 🧪 Testing

### Test Keyword Agent
```bash
cd telugu-agents
python -m agents.keyword_agent
```

### Test Prompt Agent
```bash
cd telugu-agents
python -m agents.prompt_agent
```

## 📦 Installing as a Package

For cleaner imports, install as an editable package:

```bash
cd telugu-agents
pip install -e .
```

Then use from anywhere:

```python
from agents import KeywordAgent, PromptAgent

agent = KeywordAgent()
```

## 🤝 Integration with Other Projects

### Method 1: Copy the Folder
Simply copy the entire `telugu-agents` folder to your project and install dependencies.

### Method 2: Git Submodule
Add as a git submodule:
```bash
git submodule add <repo-url> telugu-agents
```

### Method 3: Install as Package
Install directly from the folder:
```bash
pip install -e /path/to/telugu-agents
```

## 📊 Data Storage

The Keyword Agent stores statistics in:
- `data/stats/enhanced_stats.json` - Full enhanced statistics with TF-IDF scores
- `data/stats/global_stats.json` - Legacy format for backward compatibility

These files are automatically created and updated by the agent.

## 🛠️ Requirements

- Python >= 3.10
- streamlit >= 1.30.0
- google-generativeai >= 0.3.0
- pandas >= 2.0.0
- python-dotenv >= 1.0.0

## 📝 License

AGPL-3.0

## 👥 Authors

Chandamama Studio Team

## 🐛 Troubleshooting

### Import Errors
If you get import errors, make sure you're running from the `telugu-agents` directory or have installed the package with `pip install -e .`

### API Key Issues
Make sure your `.env` file contains a valid `GEMINI_API_KEY` for the Prompt Agent.

### Stats Directory Missing
The Keyword Agent requires `data/stats/` directory. It should be created automatically, but if not:
```bash
mkdir -p data/stats
```

## 📚 Learn More

For more details on each agent:
- See `agents/keyword_agent.py` for Keyword Agent implementation
- See `agents/prompt_agent.py` for Prompt Agent implementation
- Run the dashboards for interactive exploration

---

**Happy Telugu Story Processing! 🎉**
