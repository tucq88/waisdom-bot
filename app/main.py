import logging
import asyncio
import signal
import sys
from pathlib import Path

from app.bot.telegram_bot import TelegramBot
from app.core.scheduler import SchedulerService
from app.config.settings import LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent.parent / "logs" / "app.log", mode="a")
    ]
)

logger = logging.getLogger(__name__)

class Application:
    """Main application class."""

    def __init__(self):
        self.telegram_bot = TelegramBot()
        self.scheduler = SchedulerService()
        self.shutdown_event = asyncio.Event()

    async def setup(self):
        """Set up the application components."""
        # Create logs directory
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)

        # Register the bot's send_reminder method as a callback
        self.scheduler.add_reminder_callback(self.telegram_bot.send_reminder)

        # Schedule periodic reminder checks
        self.scheduler.schedule_periodic_reminders(interval_minutes=60)

        # Start the scheduler
        self.scheduler.start()

        # Start the Telegram bot
        await self.telegram_bot.start()

        logger.info("Application setup complete")

    async def shutdown(self):
        """Shut down the application components."""
        logger.info("Shutting down application...")

        # Stop the Telegram bot
        await self.telegram_bot.stop()

        # Shutdown the scheduler
        self.scheduler.shutdown()

        # Set shutdown event
        self.shutdown_event.set()

        logger.info("Application shutdown complete")

    async def run(self):
        """Run the application."""
        await self.setup()

        logger.info("Application running. Press Ctrl+C to exit.")

        # Wait for shutdown event
        await self.shutdown_event.wait()

    def handle_signal(self, sig, frame):
        """Handle OS signals."""
        logger.info(f"Received signal {sig}, shutting down...")
        asyncio.create_task(self.shutdown())

async def main():
    """Main entry point."""
    app = Application()

    # Register signal handlers
    signal.signal(signal.SIGINT, app.handle_signal)
    signal.signal(signal.SIGTERM, app.handle_signal)

    try:
        await app.run()
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())