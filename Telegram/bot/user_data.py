import json
import os

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def get_user_city(chat_id: int) -> str:
    users = load_users()
    user_id = str(chat_id)
    if user_id not in users:
        return ""
    return users[user_id].get("city", "")

def set_user_city(chat_id: int, city: str, subscribed :bool = False) -> None:
    users = load_users()
    print(city)
    if str(chat_id) not in users:
        users[str(chat_id)] = {}
    users[str(chat_id)]["city"] = city
    users[str(chat_id)]["subscribe"] = subscribed
    save_users(users)

def user_subscribed(chat_id: int) -> bool:
    users = load_users()
    return users.get(str(chat_id), {}).get("subscribe", False)

def user_unsubscribed(chat_id: int) -> bool:
    users = load_users()
    if str(chat_id) not in users:
        return False
    else:
        users[str(chat_id)]["subscribe"] = False
        save_users(users)
        return True

def subscribed_users( ) -> dict[int,str]:
    users = load_users()
    subscribed_users = dict()
    for user in users:
        if users[user]["subscribe"]:
            subscribed_users[user] = users[user]
    return subscribed_users