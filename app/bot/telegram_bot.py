import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
import io
import asyncio
from typing import List, Dict, Any, Optional
import re

from app.config.settings import TELEGRAM_BOT_TOKEN
from app.core.content_processor import ContentProcessor

logger = logging.getLogger(__name__)

class TelegramBot:
    """Telegram bot for interacting with the content service."""

    def __init__(self):
        self.processor = ContentProcessor()
        self.user_interests = {}  # Simple in-memory storage for user interests

    async def start(self):
        """Start the Telegram bot."""
        if not TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN not set. Cannot start bot.")
            return

        # Initialize bot
        self.application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

        # Register handlers
        self._register_handlers()

        # Start polling
        await self.application.initialize()
        await self.application.start_polling()

        logger.info("Telegram bot started")

    async def stop(self):
        """Stop the Telegram bot."""
        if hasattr(self, 'application'):
            await self.application.stop()
            logger.info("Telegram bot stopped")

    def _register_handlers(self):
        """Register message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("search", self._search_command))
        self.application.add_handler(CommandHandler("recap", self._recap_command))
        self.application.add_handler(CommandHandler("daily", self._daily_command))
        self.application.add_handler(CommandHandler("random", self._random_command))
        self.application.add_handler(CommandHandler("interests", self._interests_command))

        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._text_message))
        self.application.add_handler(MessageHandler(filters.Document.PDF, self._pdf_document))

        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self._button_callback))

        # Error handler
        self.application.add_error_handler(self._error_handler)

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        await update.message.reply_text(
            f"Hello {user.mention_html()}! 👋\n\n"
            f"I'm your personal research assistant. I can help you save and organize content from around the web.\n\n"
            f"Try sending me a link, a PDF, or just some text you want to save. You can also use /help to see all available commands.",
            parse_mode="HTML"
        )

    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = (
            "Here's what I can do for you:\n\n"
            "📎 *Send me links* - I'll extract content and summarize it\n"
            "📄 *Send me text* - I'll save it and extract key insights\n"
            "📁 *Send me PDFs* - I'll process and summarize them\n\n"
            "*Commands:*\n"
            "/search [query] - Search through your saved content\n"
            "/recap - Get a summary of recent content\n"
            "/daily - Get your daily digest\n"
            "/random - Get a random piece of saved content\n"
            "/interests - Set your interests for better recommendations\n"
            "/help - Show this help message\n\n"
            "You can also *ask me questions* about your saved content!"
        )

        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def _search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command."""
        query = " ".join(context.args)

        if not query:
            await update.message.reply_text(
                "Please provide a search query.\n"
                "Example: /search machine learning"
            )
            return

        await update.message.reply_text(f"🔍 Searching for: {query}")

        try:
            results = await self.processor.search(query)

            if not results:
                await update.message.reply_text("No results found. Try a different search query.")
                return

            # Format results
            result_text = f"📊 Found {len(results)} results for '{query}':\n\n"

            for i, result in enumerate(results):
                score = round(result.get("similarity", 0) * 100)
                title = result.get("title", "Untitled")
                summary = result.get("summary", "No summary available")

                result_text += f"*{i+1}. {title}*\n"
                result_text += f"Relevance: {score}%\n"
                result_text += f"{summary[:100]}...\n\n"

            # Add view buttons
            keyboard = []
            for i, result in enumerate(results[:5]):  # Limit to 5 buttons
                keyboard.append([
                    InlineKeyboardButton(f"View #{i+1}", callback_data=f"view_{result.get('content_id')}")
                ])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(result_text, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in search: {str(e)}")
            await update.message.reply_text(f"Error executing search: {str(e)}")

    async def _recap_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /recap command."""
        await update.message.reply_text("🔄 Generating your recap...")

        try:
            digest = await self.processor.get_daily_digest(limit=5)

            if not digest:
                await update.message.reply_text("No recent content to recap.")
                return

            # Format digest
            recap_text = "📋 *Your Content Recap*\n\n"

            for i, item in enumerate(digest):
                title = item.get("title", "Untitled")
                summary = item.get("summary", "No summary available")
                item_type = item.get("type", "content")

                icon = "🔔" if item_type == "reminder" else "📄"
                recap_text += f"{icon} *{title}*\n"
                recap_text += f"{summary[:100]}...\n\n"

            # Add view buttons
            keyboard = []
            for i, item in enumerate(digest[:5]):  # Limit to 5 buttons
                keyboard.append([
                    InlineKeyboardButton(f"View #{i+1}", callback_data=f"view_{item.get('id')}")
                ])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(recap_text, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in recap: {str(e)}")
            await update.message.reply_text(f"Error generating recap: {str(e)}")

    async def _daily_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /daily command."""
        await update.message.reply_text("📆 Generating your daily digest...")

        try:
            # Get digest
            digest = await self.processor.get_daily_digest(limit=5)

            # Get user interests
            user_id = str(update.effective_user.id)
            user_interests = self.user_interests.get(user_id, ["AI", "technology", "research"])

            # Get recommendations
            recommendations = await self.processor.get_recommendations(user_interests)

            if not digest and not recommendations:
                await update.message.reply_text("No content available for your daily digest.")
                return

            # Format digest
            digest_text = "🌟 *Your Daily Digest* 🌟\n\n"

            if digest:
                digest_text += "*Recent Highlights:*\n\n"

                for i, item in enumerate(digest[:3]):  # Limit to 3 items
                    title = item.get("title", "Untitled")
                    summary = item.get("summary", "No summary available")
                    item_type = item.get("type", "content")

                    icon = "🔔" if item_type == "reminder" else "📄"
                    digest_text += f"{icon} *{title}*\n"
                    digest_text += f"{summary[:100]}...\n\n"

            if recommendations:
                digest_text += "*Recommended Revisits:*\n\n"

                for i, rec in enumerate(recommendations[:2]):  # Limit to 2 recommendations
                    title = rec.get("title", "Untitled")
                    reason = rec.get("reason", "No reason available")

                    digest_text += f"💡 *{title}*\n"
                    digest_text += f"Why: {reason}\n\n"

            await update.message.reply_text(digest_text, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in daily digest: {str(e)}")
            await update.message.reply_text(f"Error generating daily digest: {str(e)}")

    async def _random_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /random command."""
        await update.message.reply_text("🎲 Finding a random saved item...")

        # This is a simplified implementation - would need proper repository access
        await update.message.reply_text(
            "Random content feature coming soon! In the meantime, try using /search or /recap."
        )

    async def _interests_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /interests command."""
        user_id = str(update.effective_user.id)

        # Get current interests
        current_interests = self.user_interests.get(user_id, [])

        if not context.args:
            # Display current interests
            if current_interests:
                interests_text = ", ".join(current_interests)
                await update.message.reply_text(
                    f"Your current interests: {interests_text}\n\n"
                    f"To update your interests, use:\n"
                    f"/interests AI, machine learning, research"
                )
            else:
                await update.message.reply_text(
                    "You haven't set any interests yet.\n\n"
                    f"To set your interests, use:\n"
                    f"/interests AI, machine learning, research"
                )
            return

        # Update interests
        new_interests = " ".join(context.args)
        interests_list = [interest.strip() for interest in re.split(r'[,;]', new_interests)]

        # Filter out empty strings
        interests_list = [interest for interest in interests_list if interest]

        if not interests_list:
            await update.message.reply_text(
                "Please provide valid interests separated by commas.\n"
                "Example: /interests AI, machine learning, research"
            )
            return

        # Store interests
        self.user_interests[user_id] = interests_list

        await update.message.reply_text(
            f"✅ Your interests have been updated:\n"
            f"{', '.join(interests_list)}\n\n"
            f"I'll use these to provide better recommendations!"
        )

    async def _text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        text = update.message.text

        # Check if it's a URL
        url_pattern = re.compile(r'https?://\S+')
        if url_pattern.search(text):
            await self._process_url(update, context)
            return

        # Check if it's a question
        if text.strip().endswith("?"):
            await self._process_question(update, context)
            return

        # Treat as content to save
        await self._process_text_content(update, context)

    async def _process_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process a URL from a message."""
        message = update.message
        text = message.text

        # Extract URL
        url_pattern = re.compile(r'https?://\S+')
        match = url_pattern.search(text)
        if not match:
            await message.reply_text("No valid URL found in the message.")
            return

        url = match.group(0)

        # Send processing message
        processing_message = await message.reply_text(f"🔄 Processing URL: {url}")

        try:
            # Process URL
            content_item = await self.processor.process_url(url)

            # Send confirmation
            response = (
                f"✅ Saved content from URL\n\n"
                f"*Title:* {content_item.title}\n"
                f"*Priority:* {content_item.priority_score:.1f}/10\n"
            )

            if content_item.summary:
                response += f"\n*Summary:*\n{content_item.summary}\n"

            if content_item.tags:
                response += f"\n*Tags:* {', '.join(content_item.tags)}\n"

            if content_item.actions:
                response += f"\n*Actions:*\n"
                for action in content_item.actions:
                    response += f"• {action}\n"

            # Update or send new message
            await processing_message.edit_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error processing URL: {str(e)}")
            await processing_message.edit_text(f"Error processing URL: {str(e)}")

    async def _process_text_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process text content from a message."""
        message = update.message
        text = message.text

        # Send processing message
        processing_message = await message.reply_text("🔄 Processing your text...")

        try:
            # Process text
            content_item = await self.processor.process_text(text)

            # Send confirmation
            response = (
                f"✅ Saved text content\n\n"
                f"*Title:* {content_item.title}\n"
            )

            if content_item.summary:
                response += f"\n*Summary:*\n{content_item.summary}\n"

            if content_item.tags:
                response += f"\n*Tags:* {', '.join(content_item.tags)}\n"

            await processing_message.edit_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            await processing_message.edit_text(f"Error processing text: {str(e)}")

    async def _process_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process a question from a message."""
        message = update.message
        question = message.text

        # Send processing message
        processing_message = await message.reply_text("🤔 Thinking about your question...")

        try:
            # Get answer
            answer = await self.processor.ask(question)

            # Send answer
            await processing_message.edit_text(
                f"*Question:* {question}\n\n"
                f"*Answer:*\n{answer}",
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            await processing_message.edit_text(f"Error answering question: {str(e)}")

    async def _pdf_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle PDF documents."""
        message = update.message
        document = message.document

        if not document.file_name.lower().endswith(".pdf"):
            await message.reply_text("Please send a valid PDF file.")
            return

        # Send processing message
        processing_message = await message.reply_text(f"🔄 Processing PDF: {document.file_name}")

        try:
            # Download file
            file = await context.bot.get_file(document.file_id)
            pdf_bytes = await file.download_as_bytearray()
            pdf_file = io.BytesIO(pdf_bytes)

            # Process PDF
            content_item = await self.processor.process_pdf(pdf_file, document.file_name)

            # Send confirmation
            response = (
                f"✅ Processed PDF: {document.file_name}\n\n"
                f"*Title:* {content_item.title}\n"
                f"*Pages:* {content_item.metadata.get('page_count', 'Unknown')}\n"
            )

            if content_item.summary:
                response += f"\n*Summary:*\n{content_item.summary}\n"

            if content_item.tags:
                response += f"\n*Tags:* {', '.join(content_item.tags)}\n"

            if content_item.actions:
                response += f"\n*Actions:*\n"
                for action in content_item.actions:
                    response += f"• {action}\n"

            await processing_message.edit_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            await processing_message.edit_text(f"Error processing PDF: {str(e)}")

    async def _button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks."""
        query = update.callback_query
        await query.answer()

        # Extract callback data
        data = query.data

        if data.startswith("view_"):
            content_id = data[5:]  # Remove "view_" prefix
            await self._show_content_detail(query, content_id)

    async def _show_content_detail(self, query, content_id: str):
        """Show content detail."""
        try:
            # Get content from repository
            content_item = self.processor.repository.get_content(content_id)

            if not content_item:
                await query.edit_message_text("Content not found.")
                return

            # Format detail message
            detail_text = f"📄 *{content_item.title}*\n\n"

            if content_item.summary:
                detail_text += f"*Summary:*\n{content_item.summary}\n\n"

            if content_item.actions:
                detail_text += f"*Actions:*\n"
                for action in content_item.actions:
                    detail_text += f"• {action}\n"
                detail_text += "\n"

            if content_item.tags:
                detail_text += f"*Tags:* {', '.join(content_item.tags)}\n\n"

            detail_text += f"*Priority:* {content_item.priority_score:.1f}/10\n"
            detail_text += f"*Type:* {content_item.content_type}\n"
            detail_text += f"*Saved:* {content_item.created_at.strftime('%Y-%m-%d %H:%M')}\n"

            if content_item.source_url:
                detail_text += f"*Source:* {content_item.source_url}\n"

            # Create back button
            keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                detail_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error showing content detail: {str(e)}")
            await query.edit_message_text(f"Error showing content detail: {str(e)}")

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Update {update} caused error: {context.error}")

    async def send_reminder(self, reminders: List[Dict[str, Any]]):
        """
        Send reminders to users.

        Args:
            reminders: List of reminder items
        """
        # This is a simplified implementation - would need user management
        # In a real app, you would track which users should receive which reminders

        if not hasattr(self, 'application') or not reminders:
            return

        # TODO: Get list of active users
        # For now, this is just a placeholder that doesn't do anything
        logger.info(f"Would send {len(reminders)} reminders to users")