import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pathlib import Path

from app.models.content import ContentItem
from app.services.vector_store import VectorStore
from app.config.settings import BASE_DIR

logger = logging.getLogger(__name__)

class ContentRepository:
    """Repository for managing content items."""

    def __init__(self):
        self.data_dir = Path(BASE_DIR) / "data" / "content"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store = VectorStore()

    def save_content(self, content_item: ContentItem) -> ContentItem:
        """
        Save a content item to the repository.

        Args:
            content_item: The content item to save

        Returns:
            The saved content item
        """
        # Save embeddings to vector store
        if not content_item.embedding_id and content_item.content:
            try:
                metadata = {
                    "title": content_item.title,
                    "content_type": content_item.content_type,
                    "priority_score": content_item.priority_score,
                    "tags": content_item.tags,
                    "created_at": content_item.created_at.isoformat()
                }

                if content_item.source_url:
                    metadata["source_url"] = content_item.source_url

                embedding_id = self.vector_store.add_document(
                    content_id=content_item.id,
                    text=content_item.content,
                    metadata=metadata
                )

                content_item.embedding_id = embedding_id
                logger.info(f"Added embedding for content: {content_item.id}")
            except Exception as e:
                logger.error(f"Error adding to vector store: {str(e)}")

        # Update timestamp
        content_item.updated_at = datetime.now()

        # Save to file
        file_path = self.data_dir / f"{content_item.id}.json"
        with open(file_path, "w") as f:
            f.write(content_item.model_dump_json(indent=2))

        logger.info(f"Saved content item: {content_item.id}")
        return content_item

    def get_content(self, content_id: str) -> Optional[ContentItem]:
        """
        Get a content item by ID.

        Args:
            content_id: ID of the content item

        Returns:
            The content item or None if not found
        """
        file_path = self.data_dir / f"{content_id}.json"
        if not file_path.exists():
            logger.warning(f"Content item not found: {content_id}")
            return None

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                content_item = ContentItem.model_validate(data)

                # Update last accessed
                content_item.update_last_accessed()
                self.save_content(content_item)

                return content_item
        except Exception as e:
            logger.error(f"Error loading content item {content_id}: {str(e)}")
            return None

    def search_content(self, query: str, n_results: int = 5,
                     filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for content using the vector store.

        Args:
            query: Search query
            n_results: Number of results to return
            filter_criteria: Optional filter criteria

        Returns:
            List of matching content items
        """
        results = self.vector_store.search(
            query=query,
            n_results=n_results,
            filter_criteria=filter_criteria
        )

        # Enrich results with full content
        enriched_results = []
        for result in results:
            content_id = result.get("content_id")
            content_item = self.get_content(content_id)

            if content_item:
                enriched_results.append({
                    **result,
                    "title": content_item.title,
                    "summary": content_item.summary,
                    "content_type": content_item.content_type,
                    "priority_score": content_item.priority_score,
                    "tags": content_item.tags,
                    "created_at": content_item.created_at.isoformat(),
                    "actions": content_item.actions,
                })

        return enriched_results

    def delete_content(self, content_id: str) -> bool:
        """
        Delete a content item.

        Args:
            content_id: ID of the content item to delete

        Returns:
            True if successful, False otherwise
        """
        file_path = self.data_dir / f"{content_id}.json"
        if not file_path.exists():
            logger.warning(f"Cannot delete: Content item not found: {content_id}")
            return False

        try:
            # Get the content to find the embedding ID
            content_item = self.get_content(content_id)

            # Delete from vector store
            if content_item and content_item.embedding_id:
                self.vector_store.delete_document(content_item.embedding_id)

            # Delete file
            os.remove(file_path)
            logger.info(f"Deleted content item: {content_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting content item {content_id}: {str(e)}")
            return False

    def list_content(self, limit: int = 20, offset: int = 0,
                   sort_by: str = "created_at", sort_desc: bool = True,
                   filter_criteria: Optional[Dict[str, Any]] = None) -> List[ContentItem]:
        """
        List content items with pagination.

        Args:
            limit: Maximum number of items to return
            offset: Offset for pagination
            sort_by: Field to sort by
            sort_desc: Whether to sort in descending order
            filter_criteria: Optional filter criteria

        Returns:
            List of content items
        """
        # Get all content files
        content_files = list(self.data_dir.glob("*.json"))

        # Load content items
        content_items = []
        for file_path in content_files:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    content_item = ContentItem.model_validate(data)

                    # Apply filter criteria if provided
                    if filter_criteria:
                        skip = False
                        for key, value in filter_criteria.items():
                            if hasattr(content_item, key):
                                item_value = getattr(content_item, key)

                                # Handle list filters (like tags)
                                if isinstance(item_value, list) and isinstance(value, str):
                                    if value not in item_value:
                                        skip = True
                                        break
                                # Handle numeric comparisons with operators
                                elif isinstance(value, dict) and all(k in ["gt", "lt", "gte", "lte", "eq"] for k in value.keys()):
                                    for op, comp_value in value.items():
                                        if op == "gt" and not item_value > comp_value:
                                            skip = True
                                        elif op == "lt" and not item_value < comp_value:
                                            skip = True
                                        elif op == "gte" and not item_value >= comp_value:
                                            skip = True
                                        elif op == "lte" and not item_value <= comp_value:
                                            skip = True
                                        elif op == "eq" and not item_value == comp_value:
                                            skip = True
                                # Simple equality
                                elif item_value != value:
                                    skip = True
                                    break

                        if skip:
                            continue

                    content_items.append(content_item)
            except Exception as e:
                logger.error(f"Error loading content file {file_path}: {str(e)}")

        # Sort content items
        if hasattr(ContentItem, sort_by):
            content_items.sort(
                key=lambda x: getattr(x, sort_by),
                reverse=sort_desc
            )

        # Apply pagination
        paginated_items = content_items[offset:offset + limit]

        return paginated_items

    def get_due_reminders(self) -> List[ContentItem]:
        """
        Get content items with due reminders.

        Returns:
            List of content items with due reminders
        """
        now = datetime.now()

        # Get all content files
        content_files = list(self.data_dir.glob("*.json"))

        # Find items with due reminders
        due_reminders = []
        for file_path in content_files:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    content_item = ContentItem.model_validate(data)

                    # Check if reminder is due
                    if content_item.reminder_date and content_item.reminder_date <= now:
                        due_reminders.append(content_item)
            except Exception as e:
                logger.error(f"Error checking reminder for {file_path}: {str(e)}")

        return due_reminders