import json
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Path to the JSON file where messages will be saved
JSON_FILE_PATH = 'messages.json'

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi! Send me a message and I will save it.')

def save_message(update: Update, context: CallbackContext) -> None:
    """Save the user message to a JSON file."""
    user_message = {
        'user_id': update.message.from_user.id,
        'username': update.message.from_user.username,
        'message_text': update.message.text,
        'date': update.message.date.isoformat()
    }

    try:
        with open(JSON_FILE_PATH, 'r') as file:
            messages = json.load(file)
    except FileNotFoundError:
        messages = []

    messages.append(user_message)

    with open(JSON_FILE_PATH, 'w') as file:
        json.dump(messages, file, indent=4)

    update.message.reply_text('Your message has been saved!')

def main() -> None:
    """Start the bot."""
    # Insert your Bot token here
    updater = Updater("YOUR_TELEGRAM_BOT_TOKEN")

    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))

    # on noncommand i.e message - save the message
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, save_message))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()
