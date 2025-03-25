#!/usr/bin/env python3
"""
Project Setup Utility

This script automates the setup of the Waisdom Bot project using uv.
It creates a virtual environment, installs dependencies,
and performs basic checks to ensure the environment is ready.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Set up the project root path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent


def check_uv_installed():
    """Check if uv is installed and accessible."""
    try:
        # Run uv --version to check if uv is installed
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        logger.info("✅ uv is installed")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.warning("❌ uv is not installed or not in PATH")
        return False


def install_uv():
    """Install uv if not already installed."""
    logger.info("Installing uv...")

    if platform.system() == "Windows":
        # Windows installation
        try:
            cmd = "powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""
            subprocess.run(cmd, shell=True, check=True)
            logger.info("✅ uv installed successfully")

            # Remind user to add to PATH if needed
            logger.info("Note: You may need to add %USERPROFILE%\\.local\\bin to your PATH")
            logger.info("Restart your terminal or command prompt after adding uv to PATH")
            return True

        except subprocess.SubprocessError as e:
            logger.error(f"❌ Failed to install uv: {e}")
            logger.info("Please install uv manually: https://github.com/astral-sh/uv")
            return False
    else:
        # macOS and Linux installation
        try:
            cmd = "curl -LsSf https://astral.sh/uv/install.sh | sh"
            subprocess.run(cmd, shell=True, check=True)
            logger.info("✅ uv installed successfully")

            # Remind user to add to PATH if needed
            logger.info("Note: You may need to add ~/.local/bin to your PATH")
            logger.info("Run: export PATH=\"$HOME/.local/bin:$PATH\"")
            return True

        except subprocess.SubprocessError as e:
            logger.error(f"❌ Failed to install uv: {e}")
            logger.info("Please install uv manually: https://github.com/astral-sh/uv")
            return False


def create_venv():
    """Create a virtual environment using uv."""
    logger.info("Creating virtual environment...")

    try:
        os.chdir(project_root)
        subprocess.run(["uv", "venv"], check=True)
        logger.info("✅ Virtual environment created at .venv")
        return True
    except subprocess.SubprocessError as e:
        logger.error(f"❌ Failed to create virtual environment: {e}")
        return False


def install_dependencies():
    """Install project dependencies using uv."""
    logger.info("Installing project dependencies...")

    try:
        os.chdir(project_root)

        # Check if requirements.txt exists
        if (project_root / "requirements.txt").exists():
            subprocess.run(["uv", "pip", "sync", "requirements.txt"], check=True)
            logger.info("✅ Dependencies installed from requirements.txt")
        # Otherwise install from setup.py
        elif (project_root / "setup.py").exists():
            subprocess.run(["uv", "pip", "install", "-e", "."], check=True)
            logger.info("✅ Dependencies installed from setup.py")
        else:
            logger.error("❌ Neither requirements.txt nor setup.py found")
            return False

        return True
    except subprocess.SubprocessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False


def install_dev_dependencies():
    """Install development dependencies."""
    logger.info("Installing development dependencies...")

    try:
        os.chdir(project_root)

        # If setup.py exists, install dev extras
        if (project_root / "setup.py").exists():
            subprocess.run(["uv", "pip", "install", "-e", ".[dev]"], check=True)
            logger.info("✅ Development dependencies installed")
        else:
            # Just install pytest as a fallback
            subprocess.run(["uv", "pip", "install", "pytest"], check=True)
            logger.info("✅ Installed pytest")

        return True
    except subprocess.SubprocessError as e:
        logger.error(f"❌ Failed to install development dependencies: {e}")
        return False


def setup_env_file():
    """Copy the .env.example file to .env if it doesn't exist."""
    env_example = project_root / ".env.example"
    env_file = project_root / ".env"

    if env_example.exists() and not env_file.exists():
        try:
            with open(env_example, 'r') as example, open(env_file, 'w') as target:
                target.write(example.read())
            logger.info("✅ Created .env file from .env.example")
            logger.info("⚠️  Don't forget to edit .env with your API keys and settings!")
            return True
        except IOError as e:
            logger.error(f"❌ Failed to create .env file: {e}")
            return False
    elif env_file.exists():
        logger.info("ℹ️  .env file already exists")
        return True
    else:
        logger.warning("❌ .env.example file not found")
        return False


def run_environment_check():
    """Run the environment check script."""
    check_script = project_root / "app" / "utils" / "check_env.py"

    if check_script.exists():
        try:
            logger.info("Running environment check...")
            subprocess.run([sys.executable, str(check_script)], check=True)
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"❌ Environment check failed: {e}")
            return False
    else:
        logger.warning("❌ Environment check script not found")
        return False


def show_activation_instructions():
    """Show instructions for activating the virtual environment."""
    if platform.system() == "Windows":
        logger.info("""
=====================================================================
🚀 Setup Complete!

To activate the virtual environment:
    .venv\\Scripts\\activate

To run the bot:
    python app/main.py
=====================================================================
""")
    else:
        logger.info("""
=====================================================================
🚀 Setup Complete!

To activate the virtual environment:
    source .venv/bin/activate

To run the bot:
    python app/main.py
=====================================================================
""")


def main():
    """Main function to set up the project."""
    logger.info("Starting Waisdom Bot setup...")

    # Check if uv is installed
    if not check_uv_installed():
        if not install_uv():
            logger.error("Aborting setup - uv installation failed")
            return False

    # Create virtual environment
    if not create_venv():
        logger.error("Aborting setup - virtual environment creation failed")
        return False

    # Install dependencies
    if not install_dependencies():
        logger.error("Aborting setup - dependency installation failed")
        return False

    # Install development dependencies
    install_dev_dependencies()

    # Set up .env file
    setup_env_file()

    # Run environment check
    run_environment_check()

    # Show activation instructions
    show_activation_instructions()

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Unexpected error during setup: {e}")
        sys.exit(1)