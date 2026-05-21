import json

DATABASE_FILE = "users.json"


def load_users():

    try:

        with open(DATABASE_FILE, "r") as f:
            return json.load(f)

    except:
        return {}


def save_user(user_id, country, language):

    data = load_users()

    data[user_id] = {
        "country": country,
        "language": language
    }

    with open(DATABASE_FILE, "w") as f:
        json.dump(data, f, indent=4)
