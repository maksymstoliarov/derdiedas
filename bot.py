import telebot
from telebot import types
import os
import word as W
from dotenv import load_dotenv
import chat
import random

load_dotenv()

bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'))
quiz_mode = False
QUIZ_QUESTIONS = 10
user_data = {}
quiz = {}


def run():
    bot.polling(non_stop=True)


def send_message(chat_id, message):
    global bot
    bot.send_message(chat_id, message, parse_mode='HTML')


@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.send_message(message.chat.id, "<b>Hello</b>\nSend German word to get article and translation\n/quiz - Start quiz\n/mistakes - Review your mistakes\n/statistic - View your stats\nDeveloper @max_stoliarov", reply_markup=types.ReplyKeyboardRemove(), parse_mode='HTML')
    chat.add_chat_id(message.chat.id)
    stop_quiz(message.chat.id)


@bot.message_handler(commands=['statistic'])
def send_statistic(message):
    user_id = message.from_user.id
    daily_words = W.get_daily_words(user_id)
    all_words = W.get_all_words(user_id)
    base_words = W.get_all_base_words()
    progress_percent = round(len(all_words) / len(base_words) * 100)
    m = W.get_mistakes_statistic(user_id)
    weakest_words = []
    weakest_words_count = 5
    for mistake in m:
        if len(weakest_words) >= weakest_words_count:
            break
        weakest_words.append(f"{mistake['count']} <b>{mistake['article']} {mistake['word']}</b> - {mistake['translation']}")

    statistic_message = f"Progress: <b>{progress_percent}</b>%\nToday learned: <b>{len(daily_words)}</b> words\nAll time learned: <b>{len(all_words)}</b> words"

    if weakest_words:
        weakest_words = '\n'.join(weakest_words)
        statistic_message += f"\n\nWeakest words:\n{weakest_words}"

    bot.send_message(message.chat.id, statistic_message, reply_markup=types.ReplyKeyboardRemove(), parse_mode='HTML')
    stop_quiz(message.chat.id)


# Quiz command handler
@bot.message_handler(commands=['start'])
def quiz_command(message):
    global quiz
    chat_id = message.chat.id
    user_data[chat_id] = {"current_question": 0, "score": 0, 'mistakes': False}
    quiz[chat_id] = W.get_quiz_words(chat_id, QUIZ_QUESTIONS)
    send_question(chat_id)


# Mistakes quiz command handler
@bot.message_handler(commands=['mistakes'])
def mistakes_command(message):
    global quiz
    chat_id = message.chat.id
    mistakes = W.get_unique_mistakes(chat_id, QUIZ_QUESTIONS)
    if not mistakes:
        send_message(chat_id, "No mistakes")
        return

    user_data[chat_id] = {"current_question": 0, "score": 0, 'mistakes': True}
    um = W.get_unique_mistakes(chat_id, QUIZ_QUESTIONS)
    random.shuffle(um)
    quiz[chat_id] = um
    send_question(chat_id)


# Function to send a question
def send_question(chat_id):
    global quiz
    current_question = user_data[chat_id]["current_question"] + 1

    total_questions = len(quiz[chat_id])

    question_data = quiz[chat_id][user_data[chat_id]["current_question"]]
    question = f'{current_question}/{total_questions} <b>{question_data["word"]}</b>'

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True)
    button_row = [types.KeyboardButton(article) for article in W.ARTICLES]
    markup.row(*button_row)

    bot.send_message(chat_id, question, reply_markup=markup, parse_mode='HTML')


def stop_quiz(chat_id):
    if chat_id in user_data:
        del user_data[chat_id]

    if chat_id in quiz:
        del quiz[chat_id]


# Callback query handler
@bot.message_handler(func=lambda message: message.chat.id in user_data and "current_question" in user_data[message.chat.id])
def handle_answer(message):
    chat_id = message.chat.id
    # prevent answering finished quiz
    if user_data[chat_id]["current_question"] >= len(quiz[chat_id]):
        print("Quiz finished")
        return

    answer = message.text

    # prevent double answers
    if "answered" in user_data[chat_id]:
        print("Already answered")
        return

    user_data[chat_id]["answered"] = True

    if answer not in W.ARTICLES:
        send_message(chat_id, "Invalid article")
        return

    current_question = user_data[chat_id]["current_question"]
    correct_answer = quiz[chat_id][current_question]["article"]
    word = quiz[chat_id][current_question]["word"]
    translation = quiz[chat_id][current_question]["translation"]

    # if correct answer is array, check if the answer is in the array
    if isinstance(correct_answer, list):
        if answer in correct_answer:
            user_data[chat_id]["score"] += 1
            send_message(chat_id, f"✅ <b>{correct_answer[0]}/{correct_answer[1]} {word}</b> - {translation} ")
        else:
            send_message(chat_id, f"❌ <b>{correct_answer[0]}/{correct_answer[1]} {word}</b> - {translation}")
            new_mistake = quiz[chat_id][current_question]
            new_mistake['user_id'] = chat_id
            new_mistake['username'] = message.from_user.username
            new_mistake['date'] = message.date
            W.add_mistake(new_mistake)
    else:
        if answer == correct_answer:
            user_data[chat_id]["score"] += 1
            send_message(chat_id, f"✅ <b>{correct_answer} {word}</b> - {translation}")
        else:
            send_message(chat_id, f"❌ <b>{correct_answer} {word}</b> - {translation}")
            new_mistake = quiz[chat_id][current_question]
            new_mistake['user_id'] = chat_id
            new_mistake['username'] = message.from_user.username
            new_mistake['date'] = message.date
            W.add_mistake(new_mistake)

    existing_base_word = W.is_word_present(word, chat_id)
    if not existing_base_word:
        new_word = quiz[chat_id][current_question]
        new_word['user_id'] = chat_id
        new_word['username'] = message.from_user.username
        new_word['date'] = message.date
        W.add_word(quiz[chat_id][current_question])

    user_data[chat_id]["current_question"] += 1
    del user_data[chat_id]["answered"]

    if user_data[chat_id]["current_question"] < len(quiz[chat_id]):
        send_question(chat_id)
    else:
        score = user_data[chat_id]["score"]
        mistakes = user_data[chat_id].get('mistakes', False)
        if not mistakes:
            finish_message = "Quiz finished"
        else:
            finish_message = "Mistakes review finished"
        bot.send_message(chat_id, f"{finish_message}! Your score is <b>{score}/{len(quiz[chat_id])}</b>", reply_markup=types.ReplyKeyboardRemove(), parse_mode='HTML')
        stop_quiz(chat_id)


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
            article = existing_word["article"]
            if isinstance(article, list):
                article = '/'.join(article)

            send_message(message.chat.id, f'<b>{article} {existing_word["word"]}</b> - {existing_word["translation"]}')
            return

        # Find the word in the base words
        existing_base_word = W.is_word_present_in_base(word)
        if existing_base_word:
            existing_base_word['user_id'] = user_id
            existing_base_word['username'] = message.from_user.username
            existing_base_word['date'] = message.date

            W.add_word(existing_base_word)
            article = existing_base_word["article"]
            if isinstance(article, list):
                article = '/'.join(article)

            send_message(message.chat.id, f"<b>{article} {word}</b> - {existing_base_word['translation']}\n<i>learned new word</i> ✅")
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
        send_message(message.chat.id, f"<b>{word_dict['article']} {word}</b> - {word_dict['translation']}\n<i>learned new word</i> ✅")
    except Exception as e:
        send_message(message.chat.id, "Error")
        print(f'Error: {e}')
