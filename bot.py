import telebot
import os
import word as W
from dotenv import load_dotenv
import chat

load_dotenv()

bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'))


def run():
    bot.polling(non_stop=True)


def send_message(chat_id, message):
    global bot
    bot.send_message(chat_id, message, parse_mode='HTML')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    send_message(message.chat.id, "Hello, send me german word")
    chat.add_chat_id(message.chat.id, message.from_user.id)


@bot.message_handler(func=lambda message: True)
def save_message(message):
    try:
        word = message.text
        word = W.normalize_word(word)

        user_id = message.from_user.id
        existing_word = W.is_word_present(word, user_id)

        if existing_word:
            send_message(message.chat.id, f'<b>{existing_word["article"]} {existing_word["word"]}</b> - {existing_word["translation"]}')
            return

        # Request the api to get the article and translation of the word
        word_dict = W.request_word(word)

        # If no translation found, return message to user
        if not word_dict or not word_dict['article'] or not word_dict['translation']:
            send_message(message.chat.id, f"{word} <i>not found</i>")
            return

        # Display message to user with article and translation
        send_message(message.chat.id, f"<b>{word_dict['article']} {word}</b> - {word_dict['translation']}")

        word_dict['user_id'] = user_id
        word_dict['username'] = message.from_user.username
        word_dict['date'] = message.date

        W.add_word(word_dict)
    except Exception as e:
        send_message(message.chat.id, "Error")
        print(f'Error: {e}')
