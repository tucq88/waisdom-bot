import pytest
from datetime import datetime, timedelta

from app.models.content import ContentItem

def test_content_item_creation():
    """Test creating a ContentItem."""

    # Create a simple content item
    content_item = ContentItem(
        title="Test Title",
        content="Test content body",
        content_type="text"
    )

    # Check basic attributes
    assert content_item.title == "Test Title"
    assert content_item.content == "Test content body"
    assert content_item.content_type == "text"
    assert content_item.id is not None
    assert isinstance(content_item.created_at, datetime)
    assert isinstance(content_item.updated_at, datetime)

def test_update_last_accessed():
    """Test updating last_accessed."""

    content_item = ContentItem(
        title="Test Title",
        content="Test content body",
        content_type="text"
    )

    # Last accessed should initially be None
    assert content_item.last_accessed is None

    # Update last accessed
    content_item.update_last_accessed()

    # Now it should be set
    assert content_item.last_accessed is not None
    assert isinstance(content_item.last_accessed, datetime)

def test_set_reminder():
    """Test setting a reminder."""

    content_item = ContentItem(
        title="Test Title",
        content="Test content body",
        content_type="text"
    )

    # Reminder date should initially be None
    assert content_item.reminder_date is None

    # Set a reminder for 3 days
    days = 3
    content_item.set_reminder(days)

    # Now it should be set to approximately 3 days in the future
    assert content_item.reminder_date is not None
    assert isinstance(content_item.reminder_date, datetime)

    # Check that it's within a minute of the expected time (to allow for test execution time)
    now = datetime.now()
    expected_time = now + timedelta(days=days)
    difference = abs((content_item.reminder_date - expected_time).total_seconds())
    assert difference < 60  # Within 60 seconds