from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Dict, Any, Optional, List, Callable, Awaitable
import logging
import asyncio

from app.core.content_repository import ContentRepository

logger = logging.getLogger(__name__)

class SchedulerService:
    """Service for scheduling and managing reminders."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.repository = ContentRepository()
        self.reminder_callbacks = []

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown")

    def add_reminder_callback(self, callback: Callable[[List[Dict[str, Any]]], Awaitable[None]]):
        """
        Register a callback for reminders.

        Args:
            callback: Async function to call with reminder items
        """
        self.reminder_callbacks.append(callback)
        logger.info(f"Registered reminder callback: {callback.__name__}")

    def schedule_daily_reminders(self, hour: int = 9, minute: int = 0):
        """
        Schedule daily reminder checks.

        Args:
            hour: Hour to run (24-hour format)
            minute: Minute to run
        """
        self.scheduler.add_job(
            self._check_reminders,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_reminders",
            replace_existing=True
        )

        logger.info(f"Scheduled daily reminders for {hour:02d}:{minute:02d}")

    def schedule_periodic_reminders(self, interval_minutes: int = 60):
        """
        Schedule periodic reminder checks.

        Args:
            interval_minutes: Interval in minutes
        """
        self.scheduler.add_job(
            self._check_reminders,
            'interval',
            minutes=interval_minutes,
            id="periodic_reminders",
            replace_existing=True
        )

        logger.info(f"Scheduled periodic reminders every {interval_minutes} minutes")

    async def _check_reminders(self):
        """Check for due reminders and notify callbacks."""
        try:
            logger.info("Checking for due reminders")

            # Get due reminders
            reminders = self.repository.get_due_reminders()

            if not reminders:
                logger.info("No due reminders found")
                return

            logger.info(f"Found {len(reminders)} due reminders")

            # Format reminders for callbacks
            formatted_reminders = []
            for item in reminders:
                formatted_reminders.append({
                    "id": item.id,
                    "title": item.title,
                    "summary": item.summary,
                    "priority_score": item.priority_score,
                    "tags": item.tags,
                    "actions": item.actions,
                    "created_at": item.created_at.isoformat()
                })

            # Call all callbacks
            for callback in self.reminder_callbacks:
                try:
                    await callback(formatted_reminders)
                except Exception as e:
                    logger.error(f"Error in reminder callback {callback.__name__}: {str(e)}")

        except Exception as e:
            logger.error(f"Error checking reminders: {str(e)}")

    def schedule_custom_job(self, job_id: str, func: Callable, **trigger_args):
        """
        Schedule a custom job.

        Args:
            job_id: Unique identifier for the job
            func: Function to execute
            trigger_args: Arguments for the trigger
        """
        self.scheduler.add_job(
            func,
            id=job_id,
            replace_existing=True,
            **trigger_args
        )

        logger.info(f"Scheduled custom job: {job_id}")