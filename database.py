from pymongo import MongoClient
from config import MONGO_URL, logger

class Database:
    def __init__(self):
        try:
            self.client = MongoClient(MONGO_URL)
            self.db = self.client['telegram_bot']
            self.messages = self.db['messages']
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    def store_message(self, text, photo_id, buttons=None):
        """Store a message with its photo and optional inline keyboard"""
        try:
            logger.info(f"Attempting to store message with text: {text[:50]}...")
            message_data = {
                'text': text,
                'photo_id': photo_id,
                'buttons': buttons or []
            }
            result = self.messages.insert_one(message_data)
            logger.info(f"Successfully stored message with ID: {result.inserted_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store message: {str(e)}")
            return False

    def get_message_by_text(self, text):
        """Retrieve a message by its text"""
        try:
            logger.info(f"Searching for message with text: {text[:50]}...")
            message = self.messages.find_one({'text': text})
            if message:
                logger.info("Message found in database")
            else:
                logger.info("No matching message found")
            return message
        except Exception as e:
            logger.error(f"Failed to retrieve message: {str(e)}")
            return None

    def close(self):
        """Close the MongoDB connection"""
        try:
            self.client.close()
            logger.info("Closed MongoDB connection")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {str(e)}")