from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_ID, CHANNEL_ID, PHOTO_TEXT, KEYBOARD_CHOICE, BUTTON_DETAILS, logger
from typing import Optional, List, Dict, Any

class MessageHandler:
    def __init__(self, db):
        self.db = db

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start command handler"""
        logger.info("Start command received")
        if not update.effective_user:
            logger.warning("No effective user found in update")
            return ConversationHandler.END

        user_id = update.effective_user.id
        logger.info(f"User {user_id} started the bot")

        if user_id != ADMIN_ID:
            logger.warning(f"Unauthorized access attempt from user {user_id}")
            await update.message.reply_text("Sorry, you're not authorized to use this bot.")
            return ConversationHandler.END

        await update.message.reply_text(
            "Welcome! Send me a photo with caption to create a new auto-response message."
        )
        return PHOTO_TEXT

    async def photo_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle photo with caption"""
        logger.info("Photo handler triggered")
        if not update.message or not update.message.photo:
            logger.warning("No photo found in update")
            return PHOTO_TEXT

        if not update.message.caption:
            logger.warning("Photo received without caption")
            await update.message.reply_text("Please send the photo with a caption!")
            return PHOTO_TEXT

        logger.info(f"Received photo with caption: {update.message.caption}")
        context.user_data['photo'] = update.message.photo[-1].file_id
        context.user_data['text'] = update.message.caption

        keyboard = ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
        await update.message.reply_text(
            "Would you like to add an inline keyboard?",
            reply_markup=keyboard
        )
        return KEYBOARD_CHOICE

    async def keyboard_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle keyboard choice"""
        logger.info("Keyboard choice handler triggered")
        if not update.message:
            logger.warning("No message found in update")
            return ConversationHandler.END

        if update.message.text.lower() == 'yes':
            logger.info("User chose to add inline keyboard")
            await update.message.reply_text(
                "Please send the button details in format:\n"
                "Button Text - https://example.com\n"
                "One button per line.",
                reply_markup=ReplyKeyboardRemove()
            )
            return BUTTON_DETAILS

        # Store message without buttons
        try:
            logger.info("Storing message without buttons")
            # Store in database
            self.db.store_message(
                context.user_data['text'],
                context.user_data['photo']
            )

            # Send to channel
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=context.user_data['photo'],
                caption=context.user_data['text']
            )
            logger.info("Message stored and sent to channel successfully")

            await update.message.reply_text("Message stored successfully!")
        except Exception as e:
            logger.error(f"Failed to store message: {str(e)}")
            await update.message.reply_text("Failed to store message. Please try again.")

        return ConversationHandler.END

    async def button_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle button details"""
        logger.info("Button details handler triggered")
        if not update.message:
            logger.warning("No message found in update")
            return ConversationHandler.END

        try:
            # Format button data
            button_data = []
            for line in update.message.text.split('\n'):
                if ' - http' in line:
                    text, url = line.split(' - ', 1)
                    if text.strip() and url.strip().startswith('http'):
                        button_data.append(line.strip())

            if not button_data:
                logger.warning("Invalid button format received")
                await update.message.reply_text(
                    "Invalid button format! Please use:\nButton Text - https://example.com"
                )
                return BUTTON_DETAILS

            logger.info(f"Creating keyboard with {len(button_data)} buttons")
            # Create keyboard
            keyboard = []
            for button in button_data:
                text, url = button.split(' - ', 1)
                keyboard.append([InlineKeyboardButton(text=text.strip(), url=url.strip())])
            markup = InlineKeyboardMarkup(keyboard)

            # Store in database
            logger.info("Storing message with buttons")
            self.db.store_message(
                context.user_data['text'],
                context.user_data['photo'],
                button_data
            )

            # Send to channel
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=context.user_data['photo'],
                caption=context.user_data['text'],
                reply_markup=markup
            )
            logger.info("Message with buttons stored and sent to channel successfully")

            await update.message.reply_text("Message stored successfully with inline keyboard!")
        except Exception as e:
            logger.error(f"Failed to store message with keyboard: {str(e)}")
            await update.message.reply_text("Failed to store message. Please try again.")

        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the conversation"""
        logger.info("Cancel command received")
        if update.message:
            await update.message.reply_text(
                "Operation cancelled.", 
                reply_markup=ReplyKeyboardRemove()
            )
        return ConversationHandler.END

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages and check for matches"""
        if not update.message:
            logger.warning("No message found in update")
            return

        try:
            logger.info(f"Checking for stored message match: {update.message.text}")
            message = self.db.get_message_by_text(update.message.text)
            if message:
                logger.info("Found matching message, preparing response")
                keyboard = None
                if message.get('buttons'):
                    keyboard = []
                    for button in message['buttons']:
                        text, url = button.split(' - ', 1)
                        keyboard.append([InlineKeyboardButton(text=text.strip(), url=url.strip())])
                    keyboard = InlineKeyboardMarkup(keyboard)

                # Get user's name for mention
                user = update.effective_user
                user_mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'

                # Format caption with user mention and horizontal line
                caption = f"{user_mention}\n{message['text']}"

                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=message['photo_id'],
                    caption=caption,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                logger.info("Matched message sent successfully")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")