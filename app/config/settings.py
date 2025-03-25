import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# LLM API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Vector DB Configuration
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", str(BASE_DIR / "data" / "chroma"))

# Create data directories if they don't exist
Path(CHROMA_PERSIST_DIRECTORY).mkdir(parents=True, exist_ok=True)

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Notion API
NOTION_API_KEY = os.getenv("NOTION_API_KEY")

# Application Settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
REMINDER_INTERVAL_DAYS = int(os.getenv("REMINDER_INTERVAL_DAYS", 3))
DEFAULT_AGENT_MODEL = os.getenv("DEFAULT_AGENT_MODEL", "gpt-4")
DEFAULT_EMBEDDING_MODEL = os.getenv("DEFAULT_EMBEDDING_MODEL", "text-embedding-3-small")
MAX_TOKENS_SUMMARY = int(os.getenv("MAX_TOKENS_SUMMARY", 300))

# Content Types
CONTENT_TYPES = {
    "ARTICLE": "article",
    "TWEET": "tweet",
    "PDF": "pdf",
    "IMAGE": "image",
    "TEXT": "text",
    "NOTION": "notion",
    "OTHER": "other"
}

# RAGFlow Configuration
RAGFLOW_API_URL = os.getenv("RAGFLOW_API_URL", "http://localhost:8000")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "")
RAGFLOW_COLLECTION_NAME = os.getenv("RAGFLOW_COLLECTION_NAME", "waisdom-content")

# Priority Scoring
PRIORITY_SCORE_THRESHOLD_HIGH = 8
PRIORITY_SCORE_THRESHOLD_MEDIUM = 5