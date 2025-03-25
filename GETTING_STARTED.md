# Getting Started with Waisdom

This guide will help you get up and running with your personal AI research assistant.

## 1. Setup

### Prerequisites
- Python 3.9+ installed on your system
- A Telegram account
- API keys for OpenAI (and optionally other LLM providers)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/waisdom-bot.git
cd waisdom-bot
```

2. Install uv (if not already installed):
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip
pip install uv
```

3. Create a virtual environment:
```bash
# Create the virtual environment
uv venv

# Activate on macOS and Linux
source .venv/bin/activate

# Activate on Windows
.venv\Scripts\activate
```

4. Install dependencies:
```bash
# Install from requirements.txt
uv pip sync requirements.txt
```

5. Create a `.env` file in the root directory:
```bash
cp .env.example .env
```

6. Edit the `.env` file with your API keys:
- `TELEGRAM_BOT_TOKEN`: Create a new bot in Telegram using [BotFather](https://t.me/BotFather) and copy the token
- `OPENAI_API_KEY`: Get your API key from [OpenAI](https://platform.openai.com/api-keys)

7. Check your environment:
```bash
python app/utils/check_env.py
```

## 2. Running the Bot

Start the bot:
```bash
python app/main.py
```

The bot will remain running until you stop it with `Ctrl+C`.

## 3. Using the Bot

1. Open Telegram and find your bot by the username you specified when creating it with BotFather
2. Start a conversation with your bot by clicking "Start" or sending `/start`

### Available Commands

- `/start` - Initialize the bot
- `/help` - Show available commands
- `/search [query]` - Search through your saved content
- `/recap` - Get a summary of recent content
- `/daily` - Get your daily digest
- `/random` - Get a random piece of saved content
- `/interests` - Set your interests for better recommendations

### Sending Content

You can send different types of content to your bot:

- **Links**: Send a URL and the bot will automatically extract and summarize the content
- **Text**: Send any text snippet to save it
- **PDFs**: Send PDF files for processing and summarization
- **Questions**: Ask a question and the bot will try to answer based on your saved content

## 4. Next Steps

Once you're comfortable with the basic features, consider:

- Modifying the summarization prompts in `app/services/llm_service.py` to customize the insights
- Adding support for additional content types
- Implementing additional integrations (like Notion export)
- Setting up scheduled backups for your data

## 5. Development

For developers working on the project:

```bash
# Install development dependencies
uv pip install pytest

# Run tests
pytest
```

## Troubleshooting

If you encounter issues:

1. Check that all environment variables are set correctly
2. Review the logs in the `logs/app.log` file
3. Make sure all dependencies are installed correctly
4. Verify your API keys are valid and have sufficient quota

### Common uv Commands

```bash
# Update uv itself (if installed via standalone installer)
uv self update

# List installed packages
uv pip list

# Upgrade packages
uv pip install --upgrade package_name

# Show package information
uv pip show package_name
```