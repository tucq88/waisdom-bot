#!/usr/bin/env python3
"""
Environment Check Utility

This script verifies that the environment is set up correctly for the application.
It checks for required environment variables and dependencies.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))

from app.config.settings import (
    TELEGRAM_BOT_TOKEN,
    OPENAI_API_KEY,
    CHROMA_PERSIST_DIRECTORY
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def check_environment():
    """Check if the environment is set up correctly."""

    logger.info("Checking environment setup...")

    # Check for required environment variables
    missing_vars = []

    if not TELEGRAM_BOT_TOKEN:
        missing_vars.append("TELEGRAM_BOT_TOKEN")

    if not OPENAI_API_KEY:
        missing_vars.append("OPENAI_API_KEY")

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please create a .env file with these variables or set them in your environment.")
        return False

    # Check for required directories
    chroma_dir = Path(CHROMA_PERSIST_DIRECTORY)
    if not chroma_dir.exists():
        logger.warning(f"ChromaDB directory does not exist: {CHROMA_PERSIST_DIRECTORY}")
        logger.info(f"Creating ChromaDB directory: {CHROMA_PERSIST_DIRECTORY}")
        chroma_dir.mkdir(parents=True, exist_ok=True)

    # Check for data directory
    data_dir = parent_dir / "data" / "content"
    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        logger.info(f"Creating data directory: {data_dir}")
        data_dir.mkdir(parents=True, exist_ok=True)

    # Check for logs directory
    logs_dir = parent_dir / "logs"
    if not logs_dir.exists():
        logger.warning(f"Logs directory does not exist: {logs_dir}")
        logger.info(f"Creating logs directory: {logs_dir}")
        logs_dir.mkdir(parents=True, exist_ok=True)

    # All checks passed
    logger.info("Environment setup complete!")
    return True

if __name__ == "__main__":
    if check_environment():
        print("✅ Environment is set up correctly!")
        sys.exit(0)
    else:
        print("❌ Environment setup failed. Check the logs for details.")
        sys.exit(1)