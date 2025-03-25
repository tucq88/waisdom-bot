import unittest
import subprocess
import json
import os
import pytest

class TestDockerContainers(unittest.TestCase):
    """Test that all required Docker containers are running."""

    @pytest.mark.skipif(not os.environ.get("TEST_DOCKER", False), reason="Docker tests disabled")
    def setUp(self):
        """Check if docker command is available."""
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            self.skipTest("Docker is not available or not running")

    def _get_containers(self):
        """Get list of running containers."""
        result = subprocess.run(
            ["docker", "ps", "--format", "{{json .}}"],
            check=True, capture_output=True, text=True
        )

        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                containers.append(json.loads(line))
        return containers

    @pytest.mark.skipif(not os.environ.get("TEST_DOCKER", False), reason="Docker tests disabled")
    def test_ragflow_container_running(self):
        """Test if RAGFlow container is running."""
        containers = self._get_containers()

        # Look for container names or images containing 'ragflow'
        ragflow_containers = [
            c for c in containers
            if 'ragflow' in c.get('Names', '').lower() or
               'ragflow' in c.get('Image', '').lower() or
               'infiniflow/ragflow' in c.get('Image', '').lower()
        ]

        self.assertTrue(
            len(ragflow_containers) > 0,
            "No RAGFlow containers found. Make sure the RAGFlow Docker container is running."
        )

    @pytest.mark.skipif(not os.environ.get("TEST_DOCKER", False), reason="Docker tests disabled")
    def test_elasticsearch_container_running(self):
        """Test if Elasticsearch container for RAGFlow is running."""
        containers = self._get_containers()

        # Look for Elasticsearch containers
        es_containers = [
            c for c in containers
            if ('elasticsearch' in c.get('Image', '').lower() or
                'elastic' in c.get('Names', '').lower()) and
               'ragflow' in c.get('Names', '').lower()
        ]

        self.assertTrue(
            len(es_containers) > 0,
            "No Elasticsearch containers found for RAGFlow. RAGFlow may not function correctly."
        )

    @pytest.mark.skipif(not os.environ.get("TEST_DOCKER", False), reason="Docker tests disabled")
    def test_minio_container_running(self):
        """Test if MinIO container for RAGFlow is running."""
        containers = self._get_containers()

        # Look for MinIO containers
        minio_containers = [
            c for c in containers
            if 'minio' in c.get('Image', '').lower() or 'minio' in c.get('Names', '').lower()
        ]

        self.assertTrue(
            len(minio_containers) > 0,
            "No MinIO containers found for RAGFlow. Document storage may not function correctly."
        )

    @pytest.mark.skipif(not os.environ.get("TEST_DOCKER", False), reason="Docker tests disabled")
    def test_mysql_container_running(self):
        """Test if MySQL container for RAGFlow is running."""
        containers = self._get_containers()

        # Look for MySQL containers
        mysql_containers = [
            c for c in containers
            if ('mysql' in c.get('Image', '').lower() or
                'mysql' in c.get('Names', '').lower()) and
               'ragflow' in c.get('Names', '').lower()
        ]

        self.assertTrue(
            len(mysql_containers) > 0,
            "No MySQL containers found for RAGFlow. RAGFlow metadata storage may not function correctly."
        )

    @pytest.mark.skipif(not os.environ.get("TEST_DOCKER", False), reason="Docker tests disabled")
    def test_redis_container_running(self):
        """Test if Redis container is running (if used)."""
        # Skip if REDIS_URL is not configured to use Docker
        redis_url = os.environ.get("REDIS_URL", "")
        if not redis_url or "localhost" not in redis_url and "127.0.0.1" not in redis_url:
            self.skipTest("Redis not configured to use local Docker")

        containers = self._get_containers()

        # Look for Redis containers
        redis_containers = [
            c for c in containers
            if 'redis' in c.get('Image', '').lower() or 'redis' in c.get('Names', '').lower()
        ]

        self.assertTrue(
            len(redis_containers) > 0,
            "No Redis containers found. Make sure the Redis Docker container is running if required."
        )


if __name__ == "__main__":
    unittest.main()