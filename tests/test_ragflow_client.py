import unittest
import os
import uuid
from dotenv import load_dotenv
import pytest
from ragflow.client import RAGFlowClient
from app.config.settings import RAGFLOW_API_URL, RAGFLOW_API_KEY, RAGFLOW_COLLECTION_NAME

# Load environment variables from .env file
load_dotenv()

@pytest.mark.skipif(not RAGFLOW_API_KEY, reason="RAGFlow API key not configured")
class TestRAGFlowClient(unittest.TestCase):
    """Test RAGFlow client functionality."""

    def setUp(self):
        """Set up RAGFlow client and test collection."""
        self.client = RAGFlowClient(
            base_url=RAGFLOW_API_URL,
            api_key=RAGFLOW_API_KEY
        )

        # Create a test collection with a unique name
        self.test_collection_name = f"test-{uuid.uuid4()}"
        self.client.create_collection(self.test_collection_name)

    def tearDown(self):
        """Clean up test collection."""
        try:
            # Delete the test collection
            self.client.delete_collection(self.test_collection_name)
        except Exception:
            pass

    def test_create_and_delete_collection(self):
        """Test creating and deleting a collection."""
        # Collection already created in setUp
        collections = self.client.list_collections()
        self.assertIn(self.test_collection_name, collections,
                      f"Test collection {self.test_collection_name} not found in collection list")

        # Test deletion happens in tearDown

    def test_add_and_search_document(self):
        """Test adding and retrieving a document."""
        # Add a test document
        test_doc = {
            "content": "This is a test document for RAGFlow integration",
            "metadata": {
                "content_id": "test-doc-1",
                "source": "test",
                "title": "Test Document"
            }
        }

        result = self.client.add_documents(
            collection_name=self.test_collection_name,
            documents=[test_doc]
        )

        self.assertTrue(result.get("success", False),
                       f"Failed to add document: {result.get('error', 'Unknown error')}")

        # Search for the document
        search_results = self.client.search(
            collection_name=self.test_collection_name,
            query="test document",
            top_k=5
        )

        self.assertTrue(len(search_results) > 0, "No search results found")

        # Check if our document is in the results
        found = False
        for result in search_results:
            if "test document" in result["content"].lower():
                found = True
                break

        self.assertTrue(found, "Added document was not found in search results")

    def test_delete_document(self):
        """Test deleting a document."""
        # Add a test document
        test_doc = {
            "content": "This is a document that will be deleted",
            "metadata": {
                "content_id": "test-doc-delete",
                "source": "test",
                "title": "Delete Test"
            }
        }

        self.client.add_documents(
            collection_name=self.test_collection_name,
            documents=[test_doc]
        )

        # Delete the document
        delete_result = self.client.delete_documents(
            collection_name=self.test_collection_name,
            filter={"metadata.content_id": "test-doc-delete"}
        )

        self.assertTrue(delete_result.get("success", False),
                       f"Failed to delete document: {delete_result.get('error', 'Unknown error')}")

        # Search to verify deletion
        search_results = self.client.search(
            collection_name=self.test_collection_name,
            query="document that will be deleted",
            top_k=5
        )

        # Check if document is no longer in results
        found = False
        for result in search_results:
            if "document that will be deleted" in result["content"].lower():
                found = True
                break

        self.assertFalse(found, "Document was not properly deleted")

    def test_generate_text(self):
        """Test generating text with RAGFlow."""
        try:
            response = self.client.generate_text(
                system_prompt="You are a helpful assistant.",
                user_prompt="What is RAGFlow?",
                relevant_docs=[]  # No relevant docs needed for this test
            )

            self.assertIsNotNone(response, "No response received from text generation")
            self.assertTrue(len(response) > 0, "Empty response received from text generation")
        except Exception as e:
            self.fail(f"Text generation failed: {str(e)}")


if __name__ == "__main__":
    unittest.main()