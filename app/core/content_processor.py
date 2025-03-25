from typing import Dict, Any, Optional, List, Tuple
import logging

from app.models.content import ContentItem
from app.services.content_enrichment import ContentEnrichmentService
from app.services.llm_service import LLMService
from app.core.content_repository import ContentRepository
from app.config.settings import REMINDER_INTERVAL_DAYS

logger = logging.getLogger(__name__)

class ContentProcessor:
    """Core processor for handling content processing pipeline."""

    def __init__(self):
        self.enrichment_service = ContentEnrichmentService()
        self.llm_service = LLMService()
        self.repository = ContentRepository()

    async def process_url(self, url: str) -> ContentItem:
        """
        Process a URL and store the extracted content.

        Args:
            url: URL to process

        Returns:
            Processed ContentItem
        """
        logger.info(f"Processing URL: {url}")

        # Extract content from URL
        title, content, metadata = self.enrichment_service.extract_from_url(url)

        # Create content item
        content_type = self.enrichment_service.detect_content_type(url=url)
        content_item = ContentItem(
            title=title,
            content=content,
            content_type=content_type,
            source_url=url,
            metadata=metadata
        )

        # Process with LLM for insights
        return await self._process_content_with_llm(content_item)

    async def process_text(self, text: str, source: Optional[str] = None) -> ContentItem:
        """
        Process a text snippet and store it.

        Args:
            text: Text content to process
            source: Optional source information

        Returns:
            Processed ContentItem
        """
        logger.info(f"Processing text: {text[:50]}...")

        # Extract content from text
        title, content, metadata = self.enrichment_service.extract_from_text(text, source)

        # Create content item
        content_item = ContentItem(
            title=title,
            content=content,
            content_type="text",
            metadata=metadata
        )

        # Process with LLM for insights
        return await self._process_content_with_llm(content_item)

    async def process_pdf(self, pdf_file, filename: str, url: Optional[str] = None) -> ContentItem:
        """
        Process a PDF file and store it.

        Args:
            pdf_file: PDF file object
            filename: Name of the file
            url: Optional source URL

        Returns:
            Processed ContentItem
        """
        logger.info(f"Processing PDF: {filename}")

        # Extract content from PDF
        title, content, metadata = self.enrichment_service.extract_from_pdf(pdf_file, url)

        # Create content item
        content_item = ContentItem(
            title=title,
            content=content,
            content_type="pdf",
            source_url=url,
            metadata=metadata
        )

        # Process with LLM for insights
        return await self._process_content_with_llm(content_item)

    async def _process_content_with_llm(self, content_item: ContentItem) -> ContentItem:
        """
        Process content with LLM for insights.

        Args:
            content_item: Content item to process

        Returns:
            Processed ContentItem
        """
        try:
            # Generate summary and insights
            summary_result = self.llm_service.summarize_content(
                content=content_item.content,
                metadata=content_item.metadata
            )

            # Update content item with LLM results
            content_item.summary = summary_result.summary
            content_item.priority_score = summary_result.priority_score
            content_item.actions = summary_result.actionable_insights
            content_item.tags = summary_result.tags

            # Set reminder based on priority
            if content_item.priority_score and content_item.priority_score >= 7:
                content_item.set_reminder(REMINDER_INTERVAL_DAYS)

            logger.info(f"Successfully processed content with LLM: {content_item.id}")
        except Exception as e:
            logger.error(f"Error processing content with LLM: {str(e)}")
            # Continue without LLM processing

        # Save to repository
        saved_item = self.repository.save_content(content_item)
        return saved_item

    async def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for content using the query.

        Args:
            query: Search query
            n_results: Number of results to return

        Returns:
            List of search results
        """
        # Search in vector store
        return self.repository.search_content(query, n_results)

    async def ask(self, question: str) -> str:
        """
        Ask a question and get an answer based on stored content.

        Args:
            question: Question to ask

        Returns:
            Answer to the question
        """
        # Search for relevant content
        relevant_content = self.repository.search_content(question, n_results=3)

        if not relevant_content:
            return "I don't have any relevant information to answer that question."

        # Generate answer using LLM
        answer = self.llm_service.generate_answer(question, relevant_content)
        return answer

    async def get_daily_digest(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get a daily digest of content.

        Args:
            limit: Maximum number of items to include

        Returns:
            List of content items for digest
        """
        # Get high priority recent content
        recent_content = self.repository.list_content(
            limit=limit,
            sort_by="created_at",
            sort_desc=True,
            filter_criteria={"priority_score": {"gte": 6}}
        )

        # Get due reminders
        reminders = self.repository.get_due_reminders()

        # Combine results
        digest_items = []

        # Add reminders first
        for item in reminders[:limit]:
            digest_items.append({
                "id": item.id,
                "title": item.title,
                "summary": item.summary,
                "type": "reminder",
                "priority_score": item.priority_score,
                "tags": item.tags,
                "actions": item.actions,
                "created_at": item.created_at.isoformat()
            })

        # Add recent content
        for item in recent_content:
            if len(digest_items) >= limit:
                break

            # Skip if already in digest
            if any(d["id"] == item.id for d in digest_items):
                continue

            digest_items.append({
                "id": item.id,
                "title": item.title,
                "summary": item.summary,
                "type": "recent",
                "priority_score": item.priority_score,
                "tags": item.tags,
                "actions": item.actions,
                "created_at": item.created_at.isoformat()
            })

        return digest_items

    async def get_recommendations(self, user_interests: List[str], limit: int = 5) -> List[Dict[str, str]]:
        """
        Get content recommendations based on user interests.

        Args:
            user_interests: List of user interest topics
            limit: Maximum number of recommendations

        Returns:
            List of recommendations
        """
        # Get recent content
        recent_content = self.repository.list_content(
            limit=20,  # Get more items for LLM to choose from
            sort_by="created_at",
            sort_desc=True
        )

        # Convert to dict format for LLM
        recent_content_dicts = []
        for item in recent_content:
            recent_content_dicts.append({
                "id": item.id,
                "title": item.title,
                "summary": item.summary,
                "tags": item.tags,
                "priority_score": item.priority_score
            })

        # Generate recommendations
        recommendations = self.llm_service.recommend_content(
            user_interests=user_interests,
            recent_content=recent_content_dicts
        )

        return recommendations[:limit]