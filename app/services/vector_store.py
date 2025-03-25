import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import uuid
import json
from typing import List, Dict, Any, Optional, Tuple

from app.config.settings import CHROMA_PERSIST_DIRECTORY, OPENAI_API_KEY, DEFAULT_EMBEDDING_MODEL

class VectorStore:
    """Vector database service for storing and retrieving embeddings."""

    def __init__(self):
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIRECTORY,
            settings=Settings(anonymized_telemetry=False)
        )

        # Set up OpenAI embedding function
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=OPENAI_API_KEY,
            model_name=DEFAULT_EMBEDDING_MODEL
        )

        # Create or get the collection
        self.collection = self.client.get_or_create_collection(
            name="content_items",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
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

        # Convert metadata to strings for ChromaDB compatibility
        serialized_metadata = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                             for k, v in metadata.items()}

        # Add document to collection
        self.collection.add(
            ids=[embedding_id],
            documents=[text],
            metadatas=[{
                "content_id": content_id,
                **serialized_metadata
            }]
        )

        return embedding_id

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
        # Convert filter criteria to ChromaDB format if provided
        where_filter = None
        if filter_criteria:
            where_filter = {k: str(v) for k, v in filter_criteria.items()}

        # Execute search
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )

        # Process results
        processed_results = []
        for i, (doc_id, document, distance) in enumerate(zip(
            results['ids'][0],
            results['documents'][0],
            results['distances'][0]
        )):
            # Extract and deserialize metadata
            metadata = results['metadatas'][0][i]
            for key, value in metadata.items():
                if key != "content_id":
                    try:
                        metadata[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        # Keep as is if not JSON serialized
                        pass

            processed_results.append({
                "id": doc_id,
                "content_id": metadata.pop("content_id"),
                "text": document,
                "similarity": 1.0 - (distance if distance is not None else 0),
                "metadata": metadata
            })

        return processed_results

    def delete_document(self, embedding_id: str) -> None:
        """
        Delete a document from the vector store.

        Args:
            embedding_id: ID of the embedding to delete
        """
        self.collection.delete(ids=[embedding_id])

    def update_document(self, embedding_id: str, text: str,
                       metadata: Dict[str, Any]) -> None:
        """
        Update a document in the vector store.

        Args:
            embedding_id: ID of the embedding to update
            text: New text content
            metadata: New metadata
        """
        # Delete the old document
        self.delete_document(embedding_id)

        # Add the updated document with the same ID
        serialized_metadata = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                             for k, v in metadata.items()}

        self.collection.add(
            ids=[embedding_id],
            documents=[text],
            metadatas=[serialized_metadata]
        )