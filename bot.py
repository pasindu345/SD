import os
import signal
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from config import BOT_TOKEN, ADMIN_ID, PHOTO_TEXT, KEYBOARD_CHOICE, BUTTON_DETAILS, validate_config, logger
from database import Database
from handlers import MessageHandler as BotMessageHandler

# Global variable for application instance
application = None

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    if application:
        logger.info("Stopping bot application...")
        application.stop()
    logger.info("Bot shutdown complete")
    exit(0)

def main():
    """Start the bot"""
    global application

    # Validate configuration
    if not validate_config():
        logger.error("Invalid configuration. Please check your environment variables.")
        return

    # Initialize database
    try:
        db = Database()
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return

    # Initialize handlers
    handler = BotMessageHandler(db)

    # Initialize bot
    try:
        application = ApplicationBuilder().token(BOT_TOKEN).build()

        # Add conversation handler
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', handler.start),
                MessageHandler(filters.PHOTO & filters.User(user_id=ADMIN_ID), handler.photo_handler)
            ],
            states={
                PHOTO_TEXT: [
                    MessageHandler(
                        filters.PHOTO & filters.CAPTION & filters.User(user_id=ADMIN_ID),
                        handler.photo_handler
                    )
                ],
                KEYBOARD_CHOICE: [
                    MessageHandler(
                        filters.TEXT & filters.User(user_id=ADMIN_ID),
                        handler.keyboard_choice
                    )
                ],
                BUTTON_DETAILS: [
                    MessageHandler(
                        filters.TEXT & filters.User(user_id=ADMIN_ID),
                        handler.button_details
                    )
                ]
            },
            fallbacks=[CommandHandler('cancel', handler.cancel)]
        )

        # Add handlers
        application.add_handler(conv_handler)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler.handle_message))
        application.add_error_handler(error_handler)

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start bot
        logger.info("Starting bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        if application:
            application.stop()
        return

if __name__ == '__main__':
    main()