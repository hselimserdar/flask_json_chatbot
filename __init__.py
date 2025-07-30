# init.py
from flask import Flask, redirect, request
from user_process import compare_passwords, get_current_user, search_for_existing_user, add_new_user
from dotenv import load_dotenv
import os
import jwt
import datetime

# Load environment variables\oload_dotenv()

debugging = os.getenv("debugging", "false").lower() == "true"
flaskDebugging = os.getenv("flaskDebugging", "false").lower() == "true"

app = Flask(__name__)
# Unified secret-key name
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-change-me')

if debugging:
    print("Debugging is enabled.")
    print("Using JWT_SECRET_KEY:", app.config['JWT_SECRET_KEY'])

@app.route('/')
def landing():
    if debugging:
        print("Landing page accessed")
    return {"message": "Welcome to the Landing Page!"}

@app.route('/login', methods=['POST'])
def login():
    user = get_current_user()
    if user:
        if debugging:
            print(f"Login called but user {user} already authenticated, redirecting")
        return redirect('/chatbot')

    data = request.get_json() or {}
    if debugging:
        print("Login data:", data)

    username = data.get('username')
    password = data.get('password')

    stored = search_for_existing_user(username)
    if debugging:
        print(f"search_for_existing_user({username}) ->", stored)
    if stored is None:
        if debugging:
            print("User not found!")
        return {"message": "User not found!"}, 404

    if not compare_passwords(username, password):
        if debugging:
            print(f"compare_passwords failed for {username}")
        return {"message": "Incorrect password!"}, 401

    payload = {
        'sub': username,
        'iat': datetime.datetime.now(datetime.timezone.utc),
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
    if debugging:
        print(f"Issued token for {username}: {token}")
    return {"token": token}

@app.route('/register', methods=['POST'])
def register():
    user = get_current_user()
    if user:
        if debugging:
            print(f"Register called but user {user} already authenticated, redirecting")
        return redirect('/chatbot')

    data = request.get_json() or {}
    if debugging:
        print("Register data:", data)

    username = data.get('username')
    password = data.get('password')

    exists = search_for_existing_user(username)
    if debugging:
        print(f"search_for_existing_user({username}) ->", exists)
    if exists is not None:
        if debugging:
            print("User already exists!")
        return {"message": "User already exists!"}, 409

    if not add_new_user(username, password):
        if debugging:
            print("add_new_user failed for", username)
        return {"message": "Registration failed!"}, 500

    if debugging:
        print("Registered new user:", username)

    payload = {
        'sub': username,
        'iat': datetime.datetime.now(datetime.timezone.utc),
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
    if debugging:
        print(f"Issued token for {username}: {token}")
    return {"token": token}

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    user = get_current_user() or "guest"
    if debugging:
        print(f"Chatbot called by {user}, payload:", request.get_json())
    return {"message": f"Hello {user}, your request was received!"}

if __name__ == '__main__':
    app.run(debug=flaskDebugging)