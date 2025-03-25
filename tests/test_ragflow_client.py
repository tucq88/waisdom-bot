import unittest
import os
import uuid
from dotenv import load_dotenv
import pytest
from ragflow_sdk import RAGFlow
from app.config.settings import RAGFLOW_API_URL, RAGFLOW_API_KEY, RAGFLOW_COLLECTION_NAME

# Load environment variables from .env file
load_dotenv()

@pytest.mark.skipif(not RAGFLOW_API_KEY, reason="RAGFlow API key not configured")
class TestRAGFlowClient(unittest.TestCase):
    """Test RAGFlow client functionality."""

    def setUp(self):
        """Set up RAGFlow client and test collection."""
        self.client = RAGFlow(
            base_url=RAGFLOW_API_URL,
            api_key=RAGFLOW_API_KEY
        )

        # Create a test dataset with a unique name
        self.test_dataset_name = f"test-{uuid.uuid4()}"
        self.dataset = self.client.create_dataset(name=self.test_dataset_name)

    def tearDown(self):
        """Clean up test dataset."""
        try:
            # Find and delete the test dataset
            datasets = self.client.list_datasets(name=self.test_dataset_name)
            if datasets:
                self.client.delete_datasets(ids=[self.dataset.id])
        except Exception:
            pass

    def test_create_and_delete_dataset(self):
        """Test creating and deleting a dataset."""
        # Dataset already created in setUp
        datasets = self.client.list_datasets(name=self.test_dataset_name)
        self.assertTrue(len(datasets) > 0,
                      f"Test dataset {self.test_dataset_name} not found in dataset list")

        # Test deletion happens in tearDown

    def test_add_and_search_document(self):
        """Test adding and retrieving a document."""
        # Add a test document
        test_doc = {
            "name": "test-doc.txt",
            "blob": "This is a test document for RAGFlow integration".encode('utf-8'),
            "metadata": {
                "content_id": "test-doc-1",
                "source": "test",
                "title": "Test Document"
            }
        }

        result = self.dataset.upload_documents([test_doc])
        self.assertTrue(len(result) > 0, "Failed to add document")

        # Wait for processing to complete (in a real test you might need to poll)

        # Retrieve chunks (search)
        chunks = self.dataset.retrieve_chunks(
            query="test document",
            limit=5
        )

        self.assertTrue(len(chunks) > 0, "No search results found")

        # Check if our document content is in the results
        found = False
        for chunk in chunks:
            if "test document" in chunk.content.lower():
                found = True
                break

        self.assertTrue(found, "Added document was not found in search results")

    def test_delete_document(self):
        """Test deleting a document."""
        # Add a test document
        test_doc = {
            "name": "test-doc-delete.txt",
            "blob": "This is a document that will be deleted".encode('utf-8'),
            "metadata": {
                "content_id": "test-doc-delete",
                "source": "test",
                "title": "Delete Test"
            }
        }

        result = self.dataset.upload_documents([test_doc])
        self.assertTrue(len(result) > 0, "Failed to add document")
        doc_id = result[0].id

        # Delete the document
        self.dataset.delete_documents([doc_id])

        # List documents to verify deletion
        docs = self.dataset.list_documents(keywords="will be deleted")
        self.assertEqual(len(docs), 0, "Document was not properly deleted")

    def test_generate_text(self):
        """Test generating text with RAGFlow."""
        try:
            # Create a chat assistant
            assistant = self.client.create_chat_assistant(
                title="Test Assistant",
                model="gpt-3.5-turbo"
            )

            # Create a session
            session = assistant.create_session(name="test-session")

            # Generate a response
            response = session.converse(
                system_prompt="You are a helpful assistant.",
                user_prompt="What is RAGFlow?"
            )

            self.assertIsNotNone(response, "No response received from text generation")
            self.assertTrue(len(response.text) > 0, "Empty response received from text generation")
        except Exception as e:
            self.fail(f"Text generation failed: {str(e)}")


if __name__ == "__main__":
    unittest.main()