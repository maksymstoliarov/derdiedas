import json
import telebot
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup

load_dotenv()

# Insert your Bot token here
bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'))

# Path to the JSON file where messages will be saved
JSON_FILE_PATH = 'words.json'
API_URL = 'https://der-artikel.de/'
ARTICLES = ['der', 'die', 'das']


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Hello, send me german word")


@bot.message_handler(func=lambda message: True)
def save_message(message):
    try:
        words = []
        # if words.json is absent, create it
        if not os.path.exists(JSON_FILE_PATH):
            with open(JSON_FILE_PATH, 'w') as file:
                json.dump({}, file)
        else:
            # if words.json is not empty, read it
            if os.path.getsize(JSON_FILE_PATH) > 0:
                with open(JSON_FILE_PATH, 'r') as file:
                    words = json.load(file)

        # Find the word in the words list
        for word in words:
            if word['word'] == message.text and word['user_id'] == message.from_user.id:
                bot.send_message(message.chat.id, "Word already present: " + word['article'] + ' ' + word['word'] + ' - ' + word['translation'])
                return

        # Request the api to get the article and translation of the word
        word_article = None
        word_translation = None
        for article in ARTICLES:
            response = requests.get(f'{API_URL}/{article}/{message.text}.html')
            if response.status_code == 200:
                # get html content of the page with BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                header = soup.find('header', {'class': 'masthead d-flex'})
                h1 = header.find('h1')
                word_article = h1.find('span').text
                word_translation = header.find('span', {'style': 'margin-top:40px;color:#444;font-weight: 700;font-size: 1.2rem;'}).text.strip()
                # remove tags from word_translation
                word_translation = word_translation.replace('engl.', '').strip()
                break

        # If no translation found, return message to user
        if not word_article or not word_translation:
            bot.send_message(message.chat.id, "Word not found")
            return

        # if word_article is not in ARTICLES, return message to user
        if word_article not in ARTICLES:
            bot.send_message(message.chat.id, "Error: Article not found")
            return

        # Display message to user with article and translation
        bot.send_message(message.chat.id, f'{word_article} {message.text} - {word_translation}')

        # Save the message to the JSON file
        user_message = {
            'user_id': message.from_user.id,
            'username': message.from_user.username,
            'word': message.text,
            'article': word_article,
            'translation': word_translation,
            'date': message.date
        }

        words.append(user_message)

        with open(JSON_FILE_PATH, 'w') as file:
            json.dump(words, file, indent=4)
    except Exception as e:
        bot.send_message(message.chat.id, "Error")
        print(f'Error: {e}')

# Start polling
bot.polling(non_stop=True)
