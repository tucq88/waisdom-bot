from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class ContentItem(BaseModel):
    """Model representing a piece of content saved by the user."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    content_type: str
    source_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    embedding_id: Optional[str] = None
    priority_score: Optional[float] = None
    actions: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    reminder_date: Optional[datetime] = None

    def update_last_accessed(self):
        """Update the last_accessed timestamp to now."""
        self.last_accessed = datetime.now()

    def set_reminder(self, days: int):
        """Set a reminder for this content item."""
        from datetime import timedelta
        self.reminder_date = datetime.now() + timedelta(days=days)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Introduction to Large Language Models",
                "content": "Large Language Models (LLMs) are...",
                "content_type": "article",
                "source_url": "https://example.com/article",
                "metadata": {"author": "Jane Doe", "word_count": 1500},
                "summary": "A clear introduction to LLMs with examples.",
                "embedding_id": "chroma-123456",
                "priority_score": 7.5,
                "actions": ["Review code examples", "Check benchmark results"],
                "tags": ["llm", "ai", "tutorial"],
                "created_at": "2023-06-01T12:00:00Z",
                "updated_at": "2023-06-01T12:00:00Z",
                "last_accessed": "2023-06-05T09:30:00Z",
                "reminder_date": "2023-06-08T12:00:00Z"
            }
        }