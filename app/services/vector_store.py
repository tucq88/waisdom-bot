import uuid
import json
from typing import List, Dict, Any, Optional, Tuple
import logging

from app.config.settings import RAGFLOW_API_URL, RAGFLOW_API_KEY, RAGFLOW_COLLECTION_NAME
from ragflow.client import RAGFlowClient

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector database service using RAGFlow for storing and retrieving embeddings."""

    def __init__(self):
        # Initialize RAGFlow client
        self.client = RAGFlowClient(
            api_url=RAGFLOW_API_URL,
            api_key=RAGFLOW_API_KEY
        )

        # Create collection if it doesn't exist
        try:
            self.client.get_collection(RAGFLOW_COLLECTION_NAME)
            logger.info(f"Using existing RAGFlow collection: {RAGFLOW_COLLECTION_NAME}")
        except Exception:
            logger.info(f"Creating new RAGFlow collection: {RAGFLOW_COLLECTION_NAME}")
            self.client.create_collection(
                name=RAGFLOW_COLLECTION_NAME,
                description="Waisdom content repository"
            )

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
        embedding_id = str(uuid.uuid4())

        # Prepare metadata with content_id
        document_metadata = {
            "content_id": content_id,
            **metadata
        }

        # Add document to RAGFlow collection
        try:
            response = self.client.add_document(
                collection_name=RAGFLOW_COLLECTION_NAME,
                document_id=embedding_id,
                content=text,
                metadata=document_metadata
            )
            logger.info(f"Added document to RAGFlow: {embedding_id}")
            return embedding_id
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
            # Execute search using RAGFlow
            search_results = self.client.search(
                collection_name=RAGFLOW_COLLECTION_NAME,
                query=query,
                limit=n_results,
                filter_criteria=filter_criteria
            )

            # Process and format results
            processed_results = []
            for result in search_results.get("results", []):
                processed_results.append({
                    "id": result.get("document_id"),
                    "content_id": result.get("metadata", {}).get("content_id"),
                    "text": result.get("content", ""),
                    "similarity": result.get("similarity", 0.0),
                    "metadata": {k: v for k, v in result.get("metadata", {}).items() if k != "content_id"}
                })

            return processed_results
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
            self.client.delete_document(
                collection_name=RAGFLOW_COLLECTION_NAME,
                document_id=embedding_id
            )
            logger.info(f"Deleted document from RAGFlow: {embedding_id}")
        except Exception as e:
            logger.error(f"Error deleting document from RAGFlow: {str(e)}")
            raise

    def update_document(self, embedding_id: str, text: str,
                       metadata: Dict[str, Any]) -> None:
        """
        Update a document in the vector store.

        Args:
            embedding_id: ID of the embedding to update
            text: New text content
            metadata: New metadata
        """
        try:
            # RAGFlow supports direct updates
            self.client.update_document(
                collection_name=RAGFLOW_COLLECTION_NAME,
                document_id=embedding_id,
                content=text,
                metadata=metadata
            )
            logger.info(f"Updated document in RAGFlow: {embedding_id}")
        except Exception as e:
            logger.error(f"Error updating document in RAGFlow: {str(e)}")
            raise