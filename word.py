import os
import json
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

# Path to the JSON file where messages will be saved
JSON_FILE_PATH = 'words.json'
API_URL = 'https://der-artikel.de/'
ARTICLES = ['der', 'die', 'das']
words = []
chat_ids = []


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


def get_daily_words(user_id):
    today = datetime.now().date()
    # get list of words for the user, for current day (from 00:00 to 23:59 as timestamp)
    today_start = int(datetime.combine(today, datetime.min.time()).timestamp())
    today_end = int(datetime.combine(today, datetime.max.time()).timestamp())

    daily_words = []
    for w in words:
        if w['user_id'] == user_id and today_start <= w['date'] <= today_end:
            daily_words.append(w)

    return daily_words


def get_all_words(user_id):
    all_words = []
    for w in words:
        if w['user_id'] == user_id:
            all_words.append(w)

    return all_words
