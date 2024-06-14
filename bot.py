import json
import telebot
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import re

load_dotenv()

# Insert your Bot token here
bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'))

# Path to the JSON file where messages will be saved
JSON_FILE_PATH = 'words.json'
API_URL = 'https://der-artikel.de/'
ARTICLES = ['der', 'die', 'das']
words = []


def request_word(word: str):
    # Request the api to get the article and translation of the word
    for article in ARTICLES:
        response = requests.get(f'{API_URL}/{article}/{word}.html')
        if response.status_code == 200:
            word_dict = {
                'word': word,
                'article': article,
                'translation': None,
            }

            try:
                # get html content of the page with BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                header = soup.find('header', {'class': 'masthead d-flex'})
                word_translation = header.find('span', {
                    'style': 'margin-top:40px;color:#444;font-weight: 700;font-size: 1.2rem;'}).text.strip()
                word_translation = word_translation.replace('engl.', '').strip()

                word_dict['translation'] = word_translation
            except Exception as e:
                print(f'Error of translation: {e}')

            return word_dict

    return None


def send_message(chat_id, message):
    global bot
    bot.send_message(chat_id, message, parse_mode='HTML')


def load_words():
    global words
    # if words.json is absent, create it
    if not os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, 'w') as file:
            json.dump([], file)
    else:
        # if words.json is not empty, read it
        if os.path.getsize(JSON_FILE_PATH) > 0:
            with open(JSON_FILE_PATH, 'r') as file:
                words = json.load(file)


def add_word(word_dict):
    global words
    words.append(word_dict)
    with open(JSON_FILE_PATH, 'w') as file:
        json.dump(words, file, indent=4)


def is_word_present(word: str, user_id: int):
    global words
    for w in words:
        if w['word'] == word and w['user_id'] == user_id:
            return w
    return None


def normalize_word(word: str):
    # tags
    word = re.sub(r'<.*?>', '', word)

    # special characters
    word = re.sub(r'[^a-zA-ZäöüÄÖÜß]', '', word)

    # trim
    word = word.strip()

    # lowercase
    word = word.lower()

    # capitalize first letter
    word = word.capitalize()

    return word


@bot.message_handler(commands=['start'])
def send_welcome(message):
    send_message(message.chat.id, "Hello, send me german word")


@bot.message_handler(func=lambda message: True)
def save_message(message):
    try:
        word = message.text
        word = normalize_word(word)

        user_id = message.from_user.id
        existing_word = is_word_present(word, user_id)

        if existing_word:
            send_message(message.chat.id, f'<b>{existing_word["article"]} {existing_word["word"]}</b> - {existing_word["translation"]}')
            return

        # Request the api to get the article and translation of the word
        word_dict = request_word(word)

        # If no translation found, return message to user
        if not word_dict or not word_dict['article'] or not word_dict['translation']:
            send_message(message.chat.id, f"{word} <i>not found</i>")
            return

        # Display message to user with article and translation
        send_message(message.chat.id, f"<b>{word_dict['article']} {word}</b> - {word_dict['translation']}")

        word_dict['user_id'] = user_id
        word_dict['username'] = message.from_user.username
        word_dict['date'] = message.date

        add_word(word_dict)
    except Exception as e:
        send_message(message.chat.id, "Error")
        print(f'Error: {e}')


if __name__ == '__main__':
    # Load words from JSON file
    load_words()

    # Start polling
    bot.polling(non_stop=True)
