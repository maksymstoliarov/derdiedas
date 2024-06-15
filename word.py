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
base_words = []
words = []
chat_ids = []


def request_word(word: str):
    # Find the word in base_words
    for base_word in base_words:
        if base_word['word'] == word:
            word_dict = {
                'word': base_word['word'],
                'article': base_word['article'],
                'translation': base_word['translation'],
            }
            return word_dict

    print("Making http request")
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
    global words, base_words
    # if words.json is absent, create it
    if not os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, 'w') as file:
            json.dump([], file)
    else:
        # if words.json is not empty, read it
        if os.path.getsize(JSON_FILE_PATH) > 0:
            with open(JSON_FILE_PATH, 'r') as file:
                words = json.load(file)

    # if base_words.json is absent, create it
    if not os.path.exists('base_words.json'):
        with open('base_words.json', 'w') as file:
            json.dump([], file)
    else:
        # if base_words.json is not empty, read it
        if os.path.getsize('base_words.json') > 0:
            with open('base_words.json', 'r') as file:
                base_words = json.load(file)


def add_word(word_dict):
    global words
    words.append(word_dict)
    with open(JSON_FILE_PATH, 'w') as file:
        json.dump(words, file, indent=4)


def add_word_base(word_dict):
    global base_words
    base_words.append(word_dict)
    with open('base_words.json', 'w') as file:
        json.dump(base_words, file, indent=4)


def is_word_present(word: str, user_id: int):
    global words
    for w in words:
        if w['word'] == word and w['user_id'] == user_id:
            return w
    return None


def is_word_present_in_base(word: str):
    global base_words
    for w in base_words:
        if w['word'] == word:
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


def get_all_base_words():
    return base_words
