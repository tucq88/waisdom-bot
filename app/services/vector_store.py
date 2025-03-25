import uuid
import json
from typing import List, Dict, Any, Optional, Tuple
import logging

from app.config.settings import RAGFLOW_API_URL, RAGFLOW_API_KEY, RAGFLOW_COLLECTION_NAME
from ragflow_sdk import RAGFlow

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector database service using RAGFlow for storing and retrieving embeddings."""

    def __init__(self):
        # Initialize RAGFlow client
        self.client = RAGFlow(
            api_key=RAGFLOW_API_KEY,
            base_url=RAGFLOW_API_URL
        )

        # Create dataset if it doesn't exist
        try:
            datasets = self.client.list_datasets(name=RAGFLOW_COLLECTION_NAME)
            if not datasets:
                self.dataset = self.client.create_dataset(name=RAGFLOW_COLLECTION_NAME)
                logger.info(f"Created new RAGFlow dataset: {RAGFLOW_COLLECTION_NAME}")
            else:
                self.dataset = datasets[0]
                logger.info(f"Using existing RAGFlow dataset: {RAGFLOW_COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Error initializing RAGFlow dataset: {str(e)}")
            raise

    def add_document(self, content_id: str, text: str, metadata: Dict[str, Any]) -> str:
        """
        Add a document to the vector store.

        Args:
            content_id: Unique identifier for the content
            text: Text to be embedded
            metadata: Additional metadata about the content

        Returns:
            embedding_id: Identifier for the embedding
        """
        # Prepare metadata with content_id
        document_metadata = {
            "content_id": content_id,
            **metadata
        }

        # Add document to RAGFlow dataset
        try:
            # Upload document as text blob with metadata
            result = self.dataset.upload_documents([{
                "display_name": f"{content_id}.txt",
                "blob": text.encode('utf-8'),
                "metadata": document_metadata
            }])

            if result and len(result) > 0:
                doc_id = result[0].id
                logger.info(f"Added document to RAGFlow: {doc_id}")
                return doc_id
            else:
                logger.error("Document upload returned no results")
                raise Exception("Document upload failed")
        except Exception as e:
            logger.error(f"Error adding document to RAGFlow: {str(e)}")
            raise

    def search(self, query: str, n_results: int = 5,
              filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query.

        Args:
            query: Search query
            n_results: Number of results to return
            filter_criteria: Optional filter criteria

        Returns:
            List of matching documents with their metadata
        """
        try:
            # RAGFlow client.retrieve doesn't support filtering by metadata directly
            # We'll retrieve all results and filter them in Python if needed
            dataset_ids = [self.dataset.id]

            # Retrieve chunks matching the query
            chunks = self.client.retrieve(
                dataset_ids=dataset_ids,
                question=query,
                page_size=n_results
            )

            # Process and format results
            processed_results = []
            for chunk in chunks:
                # Skip if filter criteria is set and doesn't match
                if filter_criteria:
                    matches_filter = True
                    for key, value in filter_criteria.items():
                        if chunk.metadata.get(key) != value:
                            matches_filter = False
                            break
                    if not matches_filter:
                        continue

                processed_results.append({
                    "id": chunk.id,
                    "content_id": chunk.metadata.get("content_id"),
                    "text": chunk.content,
                    "similarity": chunk.score,
                    "metadata": {k: v for k, v in chunk.metadata.items() if k != "content_id"}
                })

            # Limit results if we got too many after filtering
            return processed_results[:n_results]
        except Exception as e:
            logger.error(f"Error searching in RAGFlow: {str(e)}")
            return []

    def delete_document(self, embedding_id: str) -> None:
        """
        Delete a document from the vector store.

        Args:
            embedding_id: ID of the embedding to delete
        """
        try:
            # Delete document by ID
            self.dataset.delete_documents(ids=[embedding_id])
            logger.info(f"Deleted document from RAGFlow: {embedding_id}")
        except Exception as e:
            logger.error(f"Error deleting document from RAGFlow: {str(e)}")
            raise

    def update_document(self, embedding_id: str, text: str,
                       metadata: Dict[str, Any]) -> None:
        """
        Update a document in the vector store.

        Note: RAGFlow SDK doesn't have a direct update_document method.
        We'll delete and then re-add the document.

        Args:
            embedding_id: ID of the embedding to update
            text: New text content
            metadata: New metadata
        """
        try:
            # First, delete the existing document
            self.delete_document(embedding_id)

            # Then add a new document
            content_id = metadata.get("content_id", str(uuid.uuid4()))
            new_id = self.add_document(content_id, text, metadata)

            logger.info(f"Updated document in RAGFlow: {embedding_id} -> {new_id}")
        except Exception as e:
            logger.error(f"Error updating document in RAGFlow: {str(e)}")
            raise