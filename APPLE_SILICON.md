# RAGFlow Setup Guide for Apple Silicon Macs (M1/M2/M3)

RAGFlow currently doesn't provide official pre-built Docker images for ARM architecture (Apple Silicon). This guide will help you set up RAGFlow on your M1/M2/M3 Mac.

## Option 1: Build RAGFlow Docker Image for ARM (Recommended)

This approach builds a custom Docker image compatible with Apple Silicon:

```bash
# Clone the repository
git clone https://github.com/infiniflow/ragflow.git
cd ragflow/

# Download dependencies
uv run download_deps.py
# Or if uv isn't installed:
# pip install -r requirements.txt

# Build the dependencies image
docker build -f Dockerfile.deps -t infiniflow/ragflow_deps .

# Build the ARM-compatible image (lighten=1 for faster build)
docker build --build-arg LIGHTEN=1 -f Dockerfile -t infiniflow/ragflow:arm-slim .

# Run the ARM-compatible image
docker run -d --name ragflow -p 8000:8000 infiniflow/ragflow:arm-slim
```

## Option 2: Mock RAGFlow for Testing

If you're just testing or developing, you can create a simple mock server:

```python
# mock_ragflow.py
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

app = FastAPI()

@app.get("/api/v1/datasets")
async def list_datasets():
    return [{"id": "mock-dataset", "name": "test-dataset"}]

@app.post("/api/v1/datasets")
async def create_dataset(data: Dict[str, Any]):
    return {"id": "mock-dataset", "name": data.get("name", "test-dataset")}

# Add other endpoints as needed

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Run with:
```bash
python mock_ragflow.py
```

## Option 3: Using Alternative Vector Stores for Development

For development on Apple Silicon, you might consider:

1. **Using ChromaDB**: Waisdom already has ChromaDB support, which works natively on Apple Silicon:
   ```bash
   # In your .env file, ensure you're using the ChromaDB config
   # CHROMA_PERSIST_DIRECTORY=./data/chroma

   # Comment out RAGFlow settings
   # RAGFLOW_API_URL=http://localhost:8000
   # RAGFLOW_API_KEY=ragflow-dev
   ```

2. **Skip Tests**: Modify your test files to skip RAGFlow-specific tests on ARM architecture:
   ```python
   import pytest
   import platform

   @pytest.mark.skipif(platform.machine() == 'arm64',
                       reason="RAGFlow not available on ARM")
   def test_ragflow_features():
       # Test code here
   ```

## Troubleshooting

1. **Memory Issues**: If you encounter memory issues during build, increase Docker memory limits in Docker Desktop preferences.

2. **Python Version**: Ensure you're using Python 3.9+ as required by RAGFlow.

3. **Error Logs**: Check container logs for specific errors:
   ```bash
   docker logs ragflow
   ```

4. **Test Environment**: Update your .env settings for testing:
   ```
   # Test settings
   RAGFLOW_API_URL=http://localhost:8000
   RAGFLOW_API_KEY=ragflow-dev
   RAGFLOW_COLLECTION_NAME=test-collection
   ```