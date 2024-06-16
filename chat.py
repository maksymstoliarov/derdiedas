import json
import os

chat_ids = []
CHAT_IDS_FILE_PATH = 'chat_ids.json'


def load_chat_ids():
    global chat_ids
    # if chat_ids.json is absent, create it
    if not os.path.exists(CHAT_IDS_FILE_PATH):
        with open(CHAT_IDS_FILE_PATH, 'w') as file:
            json.dump([], file)
    else:
        # if chat_ids.json is not empty, read it
        if os.path.getsize(CHAT_IDS_FILE_PATH) > 0:
            with open(CHAT_IDS_FILE_PATH, 'r') as file:
                chat_ids = json.load(file)


def add_chat_id(chat_id: int):
    global chat_ids

    # check if already present
    if chat_id in chat_ids:
        return

    chat_ids.append(chat_id)
    with open(CHAT_IDS_FILE_PATH, 'w') as file:
        json.dump(chat_ids, file, indent=4)


load_chat_ids()
