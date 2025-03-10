import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
MONGO_URL = os.getenv('MONGO_URL')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
CHANNEL_ID = -1002461611033

# Conversation States
PHOTO_TEXT = 1
KEYBOARD_CHOICE = 2
BUTTON_DETAILS = 3

# Validate configuration
def validate_config():
    required_vars = ['BOT_TOKEN', 'API_ID', 'API_HASH', 'MONGO_URL', 'ADMIN_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    return True
