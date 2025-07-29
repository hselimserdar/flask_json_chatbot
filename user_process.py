import os
import sqlite3
import sys

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

debugging = os.getenv("debugging", "false").lower() == "true"
FERNET_SECRET_KEY = os.getenv("FERNET_SECRET_KEY")
assert FERNET_SECRET_KEY
FERNET = Fernet(FERNET_SECRET_KEY)

def encrypt_password(input_password):
    f = FERNET
    return f.encrypt(input_password.encode()).decode()

def decrypt_password(input_password):
    f = FERNET
    return f.decrypt(input_password.encode("utf-8")).decode("utf-8")

def compare_passwords(input_password, stored_password):
    return decrypt_password(stored_password) == input_password

def search_for_existing_user(username): #returns password if user exists
    database = sqlite3.connect('database.sqlite')
    db_cursor = database.cursor()
    try:
        db_cursor.execute("SELECT username, password FROM user")
        for user in db_cursor.fetchall():
            if user[0] == username:
                if debugging:
                    print("User found: ", user)
                    return user[1]
    except sqlite3.Error as e:
        print("SQLite error occurred:", e)
        return None
    finally:
        db_cursor.close()
        database.close()
    return None

def add_new_user(username, password):
    database = sqlite3.connect('database.sqlite')
    db_cursor = database.cursor()
    
    try:
        temp = "INSERT INTO user (username, password) VALUES ('" + str(username) + "', '" + str(password) + "')"
        print (temp)
        db_cursor.execute(temp)
        database.commit()
        return True
    except sqlite3.Error as e:
        print("SQLite error occurred:", e)
        return False
    finally:
        db_cursor.close()
        database.close()