
import base64
import hashlib
import hmac
import os
import secrets
import sqlite3
import jwt
from flask import request, current_app
from functools import wraps
from dotenv import load_dotenv

load_dotenv()
debugging = os.getenv("debugging", "false").lower() == "true"

def get_current_user():
    auth = request.headers.get('Authorization', '')
    if debugging:
        print("Authorization header:", auth)

    if auth.startswith('Bearer '):
        token = auth.split()[1]
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            if debugging:
                print("Token payload:", payload)
            if search_for_existing_user(payload.get('sub')) is not None:
                return payload.get('sub')
            else:
                if debugging:
                    print("Token is valid but user is deleted or does not exist")
                return None
        except jwt.ExpiredSignatureError:
            if debugging:
                print("Token has expired")
        except jwt.InvalidTokenError:
            if debugging:
                print("Invalid token")
    return None

def encrypt_password(user_key, input_password):
    key_bytes = base64.urlsafe_b64decode(user_key.encode('ascii'))
    tag = hmac.new(
        key_bytes,
        input_password.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(tag).decode('ascii')

def compare_passwords(username, input_password):
    conn = sqlite3.connect('database.sqlite')
    cur = conn.cursor()
    try:
        cur.execute("SELECT username, password, encryption_key FROM user")
        stored_tag = user_key = ""
        for row in cur.fetchall():
            if row[0] == username:
                stored_tag, user_key = row[1], row[2]
        recalculated = encrypt_password(user_key, input_password)
        if debugging:
            print("Recalculated tag:", recalculated)
            print("Stored tag:", stored_tag)
            print("User key:", user_key)
        return secrets.compare_digest(recalculated, stored_tag)
    finally:
        cur.close()
        conn.close()

def search_for_existing_user(username):
    conn = sqlite3.connect('database.sqlite')
    cur = conn.cursor()
    try:
        cur.execute("SELECT username, password FROM user")
        for row in cur.fetchall():
            if row[0] == username:
                if debugging:
                    print("User found:", row)
                return row[1]
    finally:
        cur.close()
        conn.close()
    return None

def add_new_user(username, password):
    conn = sqlite3.connect('database.sqlite')
    cur = conn.cursor()
    encryption_key = base64.urlsafe_b64encode(os.urandom(32)).decode('ascii')
    encrypted_password = encrypt_password(encryption_key, password)
    try:
        cur.execute(
            "INSERT INTO user (username, password, encryption_key) VALUES (?, ?, ?)",
            (username, encrypted_password, encryption_key)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error occurred:", e)
        return False
    finally:
        cur.close()
        conn.close()
