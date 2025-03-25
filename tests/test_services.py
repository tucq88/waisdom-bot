import unittest
import os
import requests
import socket
import json
import platform
from dotenv import load_dotenv
import pytest
from app.config.settings import RAGFLOW_API_URL, RAGFLOW_API_KEY

# Load environment variables from .env file
load_dotenv()

class TestServicesAvailability(unittest.TestCase):
    """Test that all required external services are available and running."""

    def test_ragflow_service_available(self):
        """Test if RAGFlow service is available and responding."""
        try:
            # Test a more reliable endpoint - just check if we can connect to the API
            response = requests.get(
                f"{RAGFLOW_API_URL}/api/v1/datasets",
                headers={"Authorization": f"Bearer {RAGFLOW_API_KEY}"},
                timeout=5
            )
            self.assertTrue(response.status_code in [200, 401, 403],
                f"RAGFlow service returned unexpected status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.fail(f"RAGFlow service is not available: {str(e)}")

    @pytest.mark.skipif(not os.environ.get("REDIS_URL"), reason="Redis URL not configured")
    def test_redis_available(self):
        """Test if Redis is available (if configured)."""
        redis_url = os.environ.get("REDIS_URL", "")
        if not redis_url:
            self.skipTest("Redis URL not configured")

        # Parse Redis URL for host and port
        # Expected format: redis://host:port
        try:
            host = redis_url.split("://")[1].split(":")[0]
            port = int(redis_url.split("://")[1].split(":")[1].split("/")[0])

            # Test connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()

            self.assertEqual(result, 0, f"Redis connection failed with error code {result}")
        except Exception as e:
            self.fail(f"Redis connection test failed: {str(e)}")

    @pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OpenAI API key not configured")
    def test_openai_api_available(self):
        """Test if OpenAI API is accessible."""
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            self.skipTest("OpenAI API key not configured")

        try:
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5
            )
            self.assertEqual(response.status_code, 200, f"OpenAI API returned {response.status_code} instead of 200")
        except requests.exceptions.RequestException as e:
            self.fail(f"OpenAI API is not available: {str(e)}")


if __name__ == "__main__":
    unittest.main()