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

- [RAGFlow](https://ragflow.io/) - Retrieval-Augmented Generation engine
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [ChromaDB](https://github.com/chroma-core/chroma)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver

## RAGFlow Integration

Waisdom uses [RAGFlow](https://ragflow.io/) as its core Retrieval-Augmented Generation (RAG) engine. RAGFlow provides:

- Advanced document understanding with fine-grained parsing for various formats including PDFs, Word documents, PowerPoint presentations, Excel spreadsheets, and more
- Superior handling of images and tables within documents
- Enhanced visibility and explainability through citation links to original content
- Customizable retrieval methods with vector and full-text search options

### Configuration

To use RAGFlow with Waisdom, add the following to your `.env` file:

```
RAGFLOW_API_URL=http://your-ragflow-server:port
RAGFLOW_API_KEY=your_api_key
RAGFLOW_COLLECTION_NAME=waisdom-content
```

### Setup Options

You can run RAGFlow in various ways:

1. **Docker Deployment**: Use the official RAGFlow Docker image:
   ```
   docker run -d --name ragflow -p 8000:8000 -e "RAGFLOW_API_KEY=your_key" infiniflow/ragflow:latest
   ```

   If you want to use Redis for caching (optional):
   ```
   # Run Redis container
   docker run -d --name waisdom-redis -p 6379:6379 redis:7.0

   # Update your .env file
   REDIS_URL=redis://localhost:6379/0
   ```

2. **Local Development Setup**: Follow the installation instructions in the [RAGFlow documentation](https://docs.ragflow.io/getting-started/installation).

For more information on RAGFlow capabilities and configuration options, visit the [official documentation](https://docs.ragflow.io/).

## Verifying Your Setup

Waisdom includes comprehensive verification tools to ensure that all required services are properly configured and running. These tests help you identify and troubleshoot issues with your environment setup.

### Running the Verification Script

```bash
# To verify services without checking Docker containers
./verify_setup.sh

# To include Docker container verification
TEST_DOCKER=1 ./verify_setup.sh
```

The verification script checks:

1. **Python Environment**: Verifies Python version and required packages
2. **Configuration**: Checks for `.env` file and required settings
3. **Services Availability**:
   - RAGFlow API connectivity
   - Redis availability (if configured)
   - OpenAI API access

4. **Docker Containers** (when `TEST_DOCKER=1`):
   - RAGFlow server
   - Elasticsearch
   - MinIO (document storage)
   - MySQL (metadata)
   - Redis (if used)

5. **RAGFlow Client Functionality**:
   - Creating and deleting collections
   - Adding and retrieving documents
   - Searching content
   - Text generation

### Running Individual Tests

You can also run specific test suites separately:

```bash
# Test service availability
python -m pytest tests/test_services.py -v

# Test Docker containers
TEST_DOCKER=1 python -m pytest tests/test_docker.py -v

# Test RAGFlow client functionality
python -m pytest tests/test_ragflow_client.py -v
```

If any tests fail, the script provides detailed error messages to help diagnose and fix issues with your setup.