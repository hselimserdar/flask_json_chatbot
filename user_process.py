import base64
import hashlib
import hmac
import os
import secrets
import sqlite3

from dotenv import load_dotenv

load_dotenv()

debugging = os.getenv("debugging", "false").lower() == "true"

def encrypt_password(user_key, input_password):
    key_bytes = base64.urlsafe_b64decode(user_key.encode('ascii'))
    tag = hmac.new(key_bytes, input_password.encode('utf-8'), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(tag).decode('ascii')

def compare_passwords(username, input_password):
    database = sqlite3.connect('database.sqlite')
    db_cursor = database.cursor()
    execute = "SELECT username, password FROM user"
    try:
        db_cursor.execute(execute)
        for user in db_cursor.fetchall():
            if user[0] == username:
                stored_tag = user[1]
                user_key = user[2]
        recalculated = encrypt_password(user_key, input_password)
        return secrets.compare_digest(recalculated, stored_tag)
    except sqlite3.Error as e:
        print("SQLite error occurred:", e)
        return False
    finally:
        db_cursor.close()
        database.close()



def search_for_existing_user(username): #returns password if user exists
    database = sqlite3.connect('database.sqlite')
    db_cursor = database.cursor()
    execute = "SELECT username, password FROM user"
    try:
        db_cursor.execute(execute)
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
    encryption_key = base64.urlsafe_b64encode(os.urandom(32)).decode('ascii')
    encrypted_password = encrypt_password(encryption_key, password)
    
    try:
        execute = "INSERT INTO user (username, password, encryption_key) VALUES ('" + str(username) + "', '" + str(password) + "', '" + str(encryption_key) + "')"
        db_cursor.execute(execute)
        database.commit()
        return True
    except sqlite3.Error as e:
        print("SQLite error occurred:", e)
        return False
    finally:
        db_cursor.close()
        database.close()