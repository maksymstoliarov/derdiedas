import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import word as W
from dotenv import load_dotenv
import chat
import random

load_dotenv()

bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'))
quiz_mode = False
QUIZ_QUESTIONS = 10

# Sample quiz questions
# quiz = [
#     {
#         "question": "What is the capital of France?",
#         "options": ["Berlin", "Paris", "Rome"],
#         "answer": "Paris"
#     },
#     {
#         "question": "What is 2 + 2?",
#         "options": ["3", "4", "5"],
#         "answer": "4"
#     },
#     {
#         "question": "What is the largest ocean on Earth?",
#         "options": ["Atlantic", "Indian", "Pacific"],
#         "answer": "Pacific"
#     }
# ]

user_data = {}
quiz = []


def run():
    bot.polling(non_stop=True)


def send_message(chat_id, message):
    global bot
    bot.send_message(chat_id, message, parse_mode='HTML')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    send_message(message.chat.id, "Hello, send me german word")
    chat.add_chat_id(message.chat.id, message.from_user.id)


@bot.message_handler(commands=['statistic'])
def send_statistic(message):
    user_id = message.from_user.id
    daily_words = W.get_daily_words(user_id)
    all_words = W.get_all_words(user_id)
    send_message(message.chat.id, f"Today added <b>{len(daily_words)}</b> words. All time <b>{len(all_words)}</b> words.")


# Quiz command handler
@bot.message_handler(commands=['quiz'])
def quiz_command(message):
    user_data[message.chat.id] = {"current_question": 0, "score": 0}
    send_question(message.chat.id)


# Function to send a question
def send_question(chat_id):
    global quiz
    all_words = W.get_all_base_words()
    # randomize the words order
    random.shuffle(all_words)
    current_question = user_data[chat_id]["current_question"] + 1

    quiz = all_words[:QUIZ_QUESTIONS]
    total_questions = len(quiz)

    question_data = quiz[user_data[chat_id]["current_question"]]
    question = f'{current_question}/{total_questions} <b>{question_data["word"]}</b>'
    # options = question_data["options"]

    # markup = types.ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True, row_width=3)
    # for article in W.ARTICLES:
    #     markup.add(types.KeyboardButton(article))

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True)
    button_row = [types.KeyboardButton(article) for article in W.ARTICLES]
    markup.row(*button_row)

    bot.send_message(chat_id, question, reply_markup=markup, parse_mode='HTML')


# Callback query handler
@bot.message_handler(func=lambda message: message.chat.id in user_data and "current_question" in user_data[message.chat.id])
def handle_answer(message):
    chat_id = message.chat.id
    answer = message.text
    current_question = user_data[chat_id]["current_question"]
    correct_answer = quiz[current_question]["article"]
    word = quiz[current_question]["word"]

    if answer == correct_answer:
        user_data[chat_id]["score"] += 1
        send_message(chat_id, f"✅ <b>{correct_answer} {word}</b>")
    else:
        send_message(chat_id, f"❌ <b>{correct_answer} {word}</b>")

    user_data[chat_id]["current_question"] += 1

    if user_data[chat_id]["current_question"] < len(quiz):
        send_question(chat_id)
    else:
        score = user_data[chat_id]["score"]
        # TODO: add mistakes to the message
        bot.send_message(chat_id, f"Quiz finished! Your score is <b>{score}/{len(quiz)}</b>", reply_markup=types.ReplyKeyboardRemove(), parse_mode='HTML')
        del user_data[chat_id]


@bot.message_handler(func=lambda message: True)
def save_message(message):
    try:
        word = message.text
        word = W.normalize_word(word)

        if not word:
            send_message(message.chat.id, "Invalid word")
            return

        user_id = message.from_user.id
        existing_word = W.is_word_present(word, user_id)

        # Find the word in the user words
        if existing_word:
            send_message(message.chat.id, f'<b>{existing_word["article"]} {existing_word["word"]}</b> - {existing_word["translation"]}')
            return

        # Find the word in the base words
        existing_base_word = W.is_word_present_in_base(word)
        if existing_base_word:
            existing_base_word['user_id'] = user_id
            existing_base_word['username'] = message.from_user.username
            existing_base_word['date'] = message.date

            W.add_word(existing_base_word)
            send_message(message.chat.id, f"<b>{existing_base_word['article']} {word}</b> - {existing_base_word['translation']}\n<i>learned new word1</i> ✅")
            return

        # Request the api to get the article and translation of the word
        word_dict = W.request_word(word)

        # If no translation found, return message to user
        if not word_dict or not word_dict['article'] or not word_dict['translation']:
            send_message(message.chat.id, f"{word} <i>not found</i>")
            return

        W.add_word_base(word_dict)

        word_dict['user_id'] = user_id
        word_dict['username'] = message.from_user.username
        word_dict['date'] = message.date

        W.add_word(word_dict)

        # Display message to user with article and translation
        send_message(message.chat.id, f"<b>{word_dict['article']} {word}</b> - {word_dict['translation']}\n<i>learned new word2</i> ✅")
    except Exception as e:
        send_message(message.chat.id, "Error")
        print(f'Error: {e}')
