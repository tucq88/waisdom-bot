#!/bin/bash

# Exit on error
set -e

echo "======================= Waisdom Setup Verification ======================="
echo "This script will verify that all required services for Waisdom are properly set up."
echo ""

# Check if Python is installed
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.9 or higher."
    exit 1
fi
python_version=$(python3 --version)
echo "✅ $python_version found"

# Check if .env file exists
echo "Checking .env file..."
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create one based on .env.example"
    exit 1
fi
echo "✅ .env file found"

# Check Python dependencies
echo "Checking Python dependencies..."
echo "Activating virtual environment if it exists..."
if [ -d ".venv" ]; then
    source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null
    echo "✅ Virtual environment activated"
else
    echo "⚠️ No virtual environment found. Using system Python."
fi

echo "Checking required packages..."
missing_packages=0
required_packages=(
    "python-telegram-bot"
    "openai"
    "ragflow-client"
    "requests"
    "beautifulsoup4"
    "pytest"
)

for package in "${required_packages[@]}"; do
    if ! python3 -c "import $package" &> /dev/null; then
        echo "❌ Package $package not found"
        missing_packages=$((missing_packages+1))
    else
        echo "✅ Package $package found"
    fi
done

if [ $missing_packages -gt 0 ]; then
    echo "⚠️ Some packages are missing. Please install them with: uv pip install -e ."
    echo "Continuing tests anyway..."
fi

# Check if Docker is available (only if TEST_DOCKER=1)
if [ "${TEST_DOCKER}" = "1" ]; then
    echo "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker not found. Docker container tests will be skipped."
    else
        docker_version=$(docker --version)
        echo "✅ $docker_version found"
        export TEST_DOCKER=1
    fi
else
    echo "ℹ️ Docker tests disabled. Set TEST_DOCKER=1 to enable."
fi

# Run the service tests
echo "======================= Running Service Tests ======================="
python3 -m pytest tests/test_services.py -v || true

# Run Docker tests if Docker is available
if [ "${TEST_DOCKER}" = "1" ]; then
    echo "======================= Running Docker Container Tests ======================="
    python3 -m pytest tests/test_docker.py -v || true
fi

# Run RAGFlow client tests
echo "======================= Running RAGFlow Client Tests ======================="
python3 -m pytest tests/test_ragflow_client.py -v || true

echo ""
echo "======================= Summary ======================="
echo "Service tests completed. Please check the output for any errors."
echo "If any tests failed, check that all services are running and properly configured."
echo ""
echo "For RAGFlow setup, ensure:"
echo "1. The RAGFlow server is running (via Docker or other means)"
echo "2. The following environment variables are set in .env:"
echo "   - RAGFLOW_API_URL"
echo "   - RAGFLOW_API_KEY"
echo "   - RAGFLOW_COLLECTION_NAME"
echo ""
echo "For Docker setup, ensure that the following containers are running:"
echo "1. ragflow-server"
echo "2. ragflow-es-01 (Elasticsearch)"
echo "3. ragflow-minio (MinIO)"
echo "4. ragflow-mysql (MySQL)"
echo "5. redis (optional, for caching - e.g., waisdom-redis)"
echo ""
echo "Note: Redis is not part of the RAGFlow stack but can be used by Waisdom for caching."
echo ""
echo "For detailed RAGFlow documentation, visit: https://ragflow.io/docs/"