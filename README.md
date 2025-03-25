# Waisdom - Personal AI Research Assistant

A powerful personal AI research assistant built around content curation, summarization, smart recall, and actionable insights.

## Features

- **Content Collection**: Telegram bot that collects links, files, and text snippets
- **Content Enrichment**: Extracts and processes content from various sources
- **Vector Database**: Stores and retrieves information semantically
- **AI Agent**: Provides summaries, extracts actionable insights, and prioritizes content
- **Smart Recall**: Resurfaces important information at optimal times

## Architecture

1. **Input Layer**: Telegram bot for collecting content
2. **Content Enrichment Layer**: Processes input for storage and analysis
3. **Vector DB + RAG Core**: Semantic storage and retrieval
4. **Agent Layer**: AI-powered processing of content
5. **Output/Recall Layer**: User interaction and smart reminders

## Getting Started

### Prerequisites

- Python 3.9+
- Telegram Bot token
- OpenAI API key (or other LLM provider)
- Redis (optional, for caching)

### Installation

#### Option 1: Automatic Setup (Recommended)

Run the automated setup script which will install uv, create a virtual environment, and install all dependencies:

```bash
# On macOS/Linux
python app/utils/setup_with_uv.py

# On Windows
python app\utils\setup_with_uv.py
```

After setup completes, activate the virtual environment as instructed.

#### Option 2: Manual Setup

1. Clone the repository
```bash
git clone https://github.com/yourusername/waisdom-bot.git
cd waisdom-bot
```

2. Install uv (if not already installed)
```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip
pip install uv
```

3. Create and activate a virtual environment
```bash
# Create virtual environment
uv venv

# Activate on macOS/Linux
source .venv/bin/activate

# Activate on Windows
.venv\Scripts\activate
```

4. Install dependencies
```bash
# Install from requirements.txt
uv pip sync requirements.txt

# Or install from pyproject.toml
uv pip install -e .
```

5. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

6. Run the bot
```bash
python app/main.py
```

## Usage

### Telegram Commands

- `/start` - Initialize the bot
- `/help` - Show available commands
- `/search [query]` - Search through your saved content
- `/recap` - Get a summary of recent content
- `/daily` - Get your daily digest
- `/random` - Get a random piece of saved content

## Development

### Project Structure

```
waisdom-bot/
├── app/
│   ├── bot/            # Telegram bot handlers
│   ├── core/           # Core functionality
│   ├── models/         # Database models
│   ├── services/       # External service integrations
│   ├── utils/          # Utility functions
│   └── config/         # Configuration
├── data/               # Data storage
└── tests/              # Test cases
```

### Testing

```bash
# Install test dependencies
uv pip install pytest

# Run tests
pytest
```

## License

MIT

## Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain)
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [ChromaDB](https://github.com/chroma-core/chroma)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver