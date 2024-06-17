import bot
import schedule
import time
import chat
import threading
import word
import os


def send_daily_summary():
    for chat_id in chat.chat_ids:
        daily_words = word.get_daily_words(chat_id)
        count = len(daily_words)
        if count == 0:
            continue

        # daily_words_string = ', '.join([f"<b>{w['article']} {w['word']}</b>" for w in daily_words])
        summary = f"You have learned <b>{count}</b> words today"
        bot.send_message(chat_id, summary)


def scheduler_ticker():
    while True:
        schedule.run_pending()
        time.sleep(1)


def run():
    scheduler_thread = threading.Thread(target=scheduler_ticker)
    scheduler_thread.start()


# Schedule the daily summary at 20:00
schedule.every().day.at(os.getenv('DAILY_SUMMARY_TIME')).do(send_daily_summary)
