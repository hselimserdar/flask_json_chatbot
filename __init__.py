# init.py
from flask import Flask, request
from chatbot_manage import chat_with_gemini, create_session_for_user, get_messages_for_session, handle_message, is_session_owner, print_sessions
from user_process import compare_passwords, get_current_user, search_for_existing_user, add_new_user
from dotenv import load_dotenv
import os
import jwt
import datetime

load_dotenv()


debugging = os.getenv("debugging", "false").lower() == "true"
flaskDebugging = os.getenv("flaskDebugging", "false").lower() == "true"

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-change-me')

if debugging:
    print("Debugging is enabled.")
    print("Using JWT_SECRET_KEY:", app.config['JWT_SECRET_KEY'])

@app.route('/')
def home():
    if debugging:
        print("Landing page accessed")
    return {"message": "Welcome to the Landing Page!"}

@app.route('/login', methods=['POST'])
def login():
    user = get_current_user()
    if user:
        if debugging:
            print(f"Login called but user {user} already authenticated, redirecting")
        return {"message" : "redirecting"} #redirect('/chatbot')    ##It will redirect to the chatbot page if the user is already authenticated - frontend will handle this

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
        return {"message" : "redirecting"} #redirect('/chatbot')    ##It will redirect to the chatbot page if the user is already authenticated - frontend will handle this

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

@app.route('/chatbot/session', methods=['GET'])
def session():
    user = get_current_user() or "guest"
    if user == "guest":
        if debugging:
            print("Chatbot accessed by guest user, no session available")
        return {"message": "No active session available for guest users."}, 404
    else:
        if debugging:
            print(f"Chatbot accessed by user {user}, returning session info")
        printed_sessions = print_sessions(user)
        if not printed_sessions:
            if debugging:
                print(f"No sessions found for user {user}")
            return {"message": "No active sessions found for user: " + str(user)}, 404
        return {"sessions": printed_sessions}

@app.route('/chatbot/message', methods=['GET'])
def session_messages():
    user = get_current_user() or "guest"
    session_id = request.args.get('session')
    if debugging:
        print(f"session_messages called by user={user}, session_id={session_id}")
    if not session_id or session_id == "" or session_id == "new":
        if debugging:
            print("No session ID provided in request")
        return {"message": "Session ID is required."}, 400
    if user == "guest":
        if debugging:
            print("User is a guest, accessing session messages is not permitted")
        return {"message": "Forbidden: Guest users cannot access session messages."}, 403
    else:
        if debugging:
            print(f"Checking if user {user} has authorized access to messages in session: {session_id}")
        if not is_session_owner(user, session_id):
            if debugging:
                print(f"User {user} is not authorized to access session: {session_id}")
            return {"message": "Forbidden: You do not have access to this session."}, 403
        else:
            if debugging:
                print(f"User {user} is authorized to access messages in session: {session_id}")
            return {" session_id": session_id, "messages": get_messages_for_session(session_id)}

@app.route('/chatbot', methods=['POST', 'GET'])
def chatbot():
    user = get_current_user() or "guest"
    message = request.get_json().get('message')
    session_id = request.args.get('session')
    if user == "guest":
        if not session_id == "guest":
            if debugging:
                print("Guest user attempted to create or access a session, which is not allowed")
            return {"message": "Guest users cannot create or access sessions."}, 403
        if debugging:
            print("Chatbot accessed by guest user, sessions will not be saved")
        return handle_message(message, chat_with_gemini(None, message, session_id=None))
    else:
        if debugging:
            print(f"Chatbot accessed by user {user}, session_id={session_id}, message={message}")
        if not session_id or session_id == "" or session_id == "new":
            if debugging:
                print("No session ID provided, creating a new session")
            session_id = create_session_for_user(user)
            if not session_id:
                if debugging:
                    print("Failed to create a new session for user:", user)
                return {"message": "Failed to create a new session."}, 500
            return handle_message(message, chat_with_gemini(user, message, session_id=session_id))
        else:
            if debugging:
                print(f"User {user} is trying to access session: {session_id}")
            if not is_session_owner(user, session_id):
                if debugging:
                    print(f"User {user} is not authorized to access session: {session_id}")
                return {"message": "Forbidden: You do not have access to this session."}, 403
            return handle_message(session_id, message, chat_with_gemini(user, message, session_id=session_id))

if __name__ == '__main__':
    app.run(debug=flaskDebugging)