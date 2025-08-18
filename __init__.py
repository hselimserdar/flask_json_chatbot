from flask import Flask, request, render_template, redirect
from chatbot_manage import chat_with_gpt, create_session_for_user, update_session_title
from user_process import compare_passwords, get_current_user, search_for_existing_user, add_new_user
from db_utilities import (get_messages_for_session, is_session_owner,
                         delete_session_for_user, get_session_id_for_message,
                         print_sessions, get_user_id, get_message_by_id)
from dotenv import load_dotenv
import os
import jwt
import datetime
import sqlite3

load_dotenv()

debugging = os.getenv("debugging", "false").lower() == "true"
flaskDebugging = os.getenv("flaskDebugging", "false").lower() == "true"

app = Flask(__name__)
flaskIP, flaskPort = os.getenv("flaskIP", "127.0.0.1"), int(os.getenv("flaskPort", 5000))
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-change-me')

if debugging:
    print("Debugging is enabled.")
    print("Using JWT_SECRET_KEY:", app.config['JWT_SECRET_KEY'])

@app.route('/')
def home():
    if debugging:
        print("Landing page accessed")
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    user = get_current_user()
    if user:
        if debugging:
            print(f"Login called but user {user} already authenticated, redirecting")
        return {"message" : "redirecting"}

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
        return {"message" : "redirecting"}

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
    page = int(request.args.get('page') or 1)
    if user == "guest":
        if debugging:
            print("Chatbot accessed by guest user, no session available")
        return {"message": "No active session available for guest users."}, 404
    else:
        if debugging:
            print(f"Chatbot accessed by user {user}, returning session info")
        printed_sessions = print_sessions(user, page)
        if not printed_sessions:
            if debugging:
                print(f"No sessions found for user {user}")
            return {"message": "No active sessions found for user: " + str(user)}, 404
        return printed_sessions
    
@app.route('/chatbot/delete', methods=['GET'])
def delete_session():
    user = get_current_user() or "guest"
    session_id = request.args.get('session')

    if debugging:
        print(f"delete_session called by user={user}, session_id={session_id}")

    if not session_id:
        if debugging:
            print("No session ID provided")
        return {"message": "Session ID is required."}, 400

    if user == "guest":
        if debugging:
            print("Guest user attempted to delete a session")
        return {"message": "Forbidden: Guests cannot delete sessions."}, 403

    if debugging:
        print(f"Checking ownership: user='{user}', session_id='{session_id}'")
    
    ownership_result = is_session_owner(user, session_id)
    if debugging:
        print(f"Ownership check result: {ownership_result}")
    
    if not ownership_result:
        if debugging:
            print(f"User {user} is not owner of session {session_id}")
        return {"message": "Forbidden: You do not have access to delete this session."}, 403

    success = delete_session_for_user(user, session_id)
    if success:
        if debugging:
            print(f"Session {session_id} deleted for user {user}")
        return {"message": f"Session {session_id} deleted successfully."}
    else:
        if debugging:
            print(f"Failed to delete session {session_id} for user {user}")
        return {"message": "Internal error: could not delete session."}, 500

@app.route('/chatbot/message', methods=['GET'])
def session_messages():
    user = get_current_user() or "guest"
    session_id = request.args.get('session')
    tree_path = request.args.get('tree')
    if debugging:
        print(f"session_messages called by user={user}, session_id={session_id}, tree_path={tree_path}")
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
            return get_messages_for_session(session_id, tree_path)

@app.route('/chatbot', methods=['POST', 'GET'])
def chatbot():
    user = get_current_user() or "guest"
    
    json_data = request.get_json() or {}
    message = json_data.get('message')
    parent_message_id = json_data.get('parent_message_id')
    session_id = request.args.get('session')
    
    if not message or not message.strip():
        if debugging:
            print("Empty or missing message received")
        return {"message": "Message content is required."}, 400
    
    if user == "guest":
        if not session_id == "guest":
            if debugging:
                print("Guest user attempted to create or access a session, which is not allowed")
            return {"message": "Guest users cannot create or access sessions."}, 403
        if debugging:
            print("Chatbot accessed by guest user, sessions will not be saved")
            print("Prompt:", message)
        reply = chat_with_gpt(user, message, session_id=None, first_message=True)
        if debugging:
            print("Reply from the API:", reply)

        if not reply:
            if debugging:
                print("Failed to get a reply from the API")
            return {"message": "Failed to get a reply from the API."}, 500
        elif isinstance(reply, dict) and reply.get("error"):
            if debugging:
                print(f"API error: {reply.get('message')}")
            return {"message": reply.get("message", "Failed to get a reply from the API.")}, 500
        
        return reply
    else:
        if debugging:
            print(f"Chatbot accessed by user {user}, session_id={session_id}, message={message}, parent_message_id={parent_message_id}")
        
        if parent_message_id:
            actual_session_id = get_session_id_for_message(parent_message_id)
            if not actual_session_id:
                if debugging:
                    print(f"Parent message {parent_message_id} not found")
                return {"message": "Parent message not found."}, 404
            if debugging:
                print(f"Using session {actual_session_id} from parent message {parent_message_id}")
            session_id = actual_session_id
        
        if not session_id or session_id == "" or session_id == "new":
            if debugging:
                print("No session ID provided, creating a new session")
            session_id = create_session_for_user(user)
            if not session_id:
                if debugging:
                    print("Failed to create a new session for user:", user)
                return {"message": "Failed to create a new session."}, 500
            reply = chat_with_gpt(user, message, session_id=session_id, first_message=True)
            
            if not reply:
                if debugging:
                    print("Failed to get a reply from the API")
                delete_session_for_user(user, session_id)
                return {"message": "Failed to get a reply from the API."}, 500
            elif isinstance(reply, dict) and reply.get("error"):
                if debugging:
                    print(f"API error: {reply.get('message')}")
                delete_session_for_user(user, session_id)
                return {"message": reply.get("message", "Failed to get a reply from the API.")}, 500
            
            return reply
        else:
            if debugging:
                print(f"User {user} is trying to access session: {session_id}")
            
            if not is_session_owner(user, session_id):
                if debugging:
                    print(f"User {user} is not authorized to access session: {session_id}")
                return {"message": "Forbidden: You do not have access to this session."}, 403
            reply = chat_with_gpt(user, message, session_id=session_id, first_message=False, parent_message_id=parent_message_id)
            
            if not reply:
                if parent_message_id:
                    if debugging:
                        print(f"Branching failed for parent_message_id: {parent_message_id}")
                    return {"message": "Forbidden: Cannot branch from the first message."}, 403
                else:
                    if debugging:
                        print("Failed to get a reply from the API for session:", session_id)
                    return {"message": "Failed to get a reply from the API."}, 500
            elif isinstance(reply, dict) and reply.get("error"):
                if debugging:
                    print(f"API error: {reply.get('message')}")
                return {"message": reply.get("message", "Failed to get a reply from the API.")}, 500
            
            return reply

@app.route('/login')
def login_page():

    user = get_current_user()
    if user:
        if debugging:
            print(f"Authenticated user {user} trying to access login page, redirecting to main chatbot")
        return redirect('/chatbot.html')
    return render_template('login.html')

@app.route('/register')
def register_page():

    user = get_current_user()
    if user:
        if debugging:
            print(f"Authenticated user {user} trying to access register page, redirecting to main chatbot")
        return redirect('/chatbot.html')
    return render_template('register.html')

@app.route('/guest-chat')
def guest_chat_page():

    user = get_current_user()
    if user:
        if debugging:
            print(f"Authenticated user {user} trying to access guest chat, redirecting to main chatbot")
        return redirect('/chatbot.html')
    return render_template('guest-chat.html')

@app.route('/verify-token', methods=['POST'])
def verify_token():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            if debugging:
                print("No valid Authorization header found")
            return {"message": "No token provided"}, 401
        
        token = auth_header.split(' ')[1]
        if debugging:
            print(f"Verifying token: {token[:20]}...")
        
        try:
            payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            username = payload.get('sub')
            issued_at = payload.get('iat')
            expires_at = payload.get('exp')
            
            if debugging:
                print(f"Token decoded successfully for user: {username}")
                print(f"Token issued at: {datetime.datetime.fromtimestamp(issued_at)}")
                print(f"Token expires at: {datetime.datetime.fromtimestamp(expires_at)}")
            
            user_exists = search_for_existing_user(username)
            if user_exists is None:
                if debugging:
                    print(f"User {username} no longer exists in database")
                return {"message": "User not found"}, 404
            
            current_time = datetime.datetime.now(datetime.timezone.utc)
            expires_datetime = datetime.datetime.fromtimestamp(expires_at, datetime.timezone.utc)
            issued_datetime = datetime.datetime.fromtimestamp(issued_at, datetime.timezone.utc)
            
            time_remaining = expires_datetime - current_time
            total_lifetime = expires_datetime - issued_datetime
            
            remaining_percentage = (time_remaining.total_seconds() / total_lifetime.total_seconds()) * 100
            
            return {
                "valid": True,
                "username": username,
                "issued_at": datetime.datetime.fromtimestamp(issued_at).isoformat(),
                "expires_at": datetime.datetime.fromtimestamp(expires_at).isoformat(),
                "time_remaining_seconds": int(time_remaining.total_seconds()),
                "time_remaining_minutes": int(time_remaining.total_seconds() / 60),
                "total_lifetime_seconds": int(total_lifetime.total_seconds()),
                "remaining_percentage": round(remaining_percentage, 2),
                "needs_refresh": remaining_percentage < 20
            }
            
        except jwt.ExpiredSignatureError:
            if debugging:
                print("Token has expired")
            return {"message": "Token expired"}, 401
        except jwt.InvalidTokenError as e:
            if debugging:
                print(f"Invalid token error: {e}")
            return {"message": "Invalid token"}, 401
            
    except Exception as e:
        if debugging:
            print(f"Token verification error: {e}")
        return {"message": "Token verification failed"}, 500

@app.route('/refresh-token', methods=['POST'])
def refresh_token():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            if debugging:
                print("No valid Authorization header found for token refresh")
            return {"message": "No token provided"}, 401
        
        token = auth_header.split(' ')[1]
        if debugging:
            print(f"Refreshing token: {token[:20]}...")
        
        try:
            payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            username = payload.get('sub')
            
        except jwt.ExpiredSignatureError:

            try:
                payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'], options={"verify_exp": False})
                username = payload.get('sub')
                expires_at = payload.get('exp')
                
                current_time = datetime.datetime.now(datetime.timezone.utc)
                expires_datetime = datetime.datetime.fromtimestamp(expires_at, datetime.timezone.utc)
                time_since_expiry = current_time - expires_datetime
                
                if time_since_expiry.total_seconds() > 300:
                    if debugging:
                        print(f"Token expired too long ago: {time_since_expiry}")
                    return {"message": "Token expired too long ago, please log in again"}, 401
                    
                if debugging:
                    print(f"Token expired {time_since_expiry.total_seconds()} seconds ago, allowing refresh")
                    
            except jwt.InvalidTokenError as e:
                if debugging:
                    print(f"Invalid token error during refresh: {e}")
                return {"message": "Invalid token"}, 401
                
        except jwt.InvalidTokenError as e:
            if debugging:
                print(f"Invalid token error during refresh: {e}")
            return {"message": "Invalid token"}, 401
        
        user_exists = search_for_existing_user(username)
        if user_exists is None:
            if debugging:
                print(f"User {username} no longer exists in database during refresh")
            return {"message": "User not found"}, 404
        
        new_payload = {
            'sub': username,
            'iat': datetime.datetime.now(datetime.timezone.utc),
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        }
        new_token = jwt.encode(new_payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
        if debugging:
            print(f"Generated new token for {username}: {new_token[:20]}...")
            
        return {
            "token": new_token,
            "username": username,
            "expires_at": new_payload['exp'].isoformat(),
            "message": "Token refreshed successfully"
        }
        
    except Exception as e:
        if debugging:
            print(f"Token refresh error: {e}")
        return {"message": "Token refresh failed"}, 500

@app.route('/chatbot/edit-message', methods=['POST'])
def edit_message():
    user = get_current_user() or "guest"
    data = request.get_json() or {}
    session_id = data.get('session_id')
    message_id = data.get('message_id')
    new_message = data.get('message')
    
    if debugging:
        print(f"edit_message called by user={user}, session_id={session_id}, message_id={message_id}, new_message={new_message}")
    
    if user == "guest":
        if debugging:
            print("Guest user attempted to edit a message")
        return {"message": "Forbidden: Guest users cannot edit messages."}, 403
    
    if not session_id or not message_id or not new_message:
        if debugging:
            print("Missing required parameters for message edit")
        return {"message": "session_id, message_id, and message are required."}, 400
    
    if not is_session_owner(user, session_id):
        if debugging:
            print(f"User {user} is not authorized to edit messages in session: {session_id}")
        return {"message": "Forbidden: You do not have access to this session."}, 403
    
    try:
        original_message = get_message_by_id(message_id)
        if not original_message:
            if debugging:
                print(f"Message {message_id} not found")
            return {"message": "Message not found."}, 404
        
        if original_message['sender'] != 'user':
            if debugging:
                print(f"Attempted to edit non-user message {message_id}")
            return {"message": "Only user messages can be edited."}, 400
        
        parent_message_id = original_message['connected_from']
        if parent_message_id == 'main':
            if debugging:
                print(f"Attempted to edit root message {message_id}")
            return {"message": "Root message cannot be edited."}, 400
        
        reply = chat_with_gpt(user, new_message, session_id=session_id, first_message=False, parent_message_id=parent_message_id)

        if not reply:
            if debugging:
                print("Failed to get a reply from GPT API for edited message")
            return {"message": "Failed to get a reply from the API."}, 500
        elif isinstance(reply, dict) and reply.get("error"):
            if debugging:
                print(f"API error during message edit: {reply.get('message')}")
            return {"message": reply.get("message", "Failed to get a reply from the API.")}, 500
        
        return reply
        
    except Exception as e:
        if debugging:
            print(f"Error in edit_message: {e}")
        return {"message": "Internal server error during message edit."}, 500

@app.route('/chatbot/save-tree-path', methods=['POST'])
def save_tree_path():
    try:
        user = get_current_user() or "guest"
        
        if user == "guest":
            return {"error": "Forbidden: Guest users cannot save tree paths."}, 403
        
        data = request.get_json() or {}
        session_id = data.get('session_id')
        tree_path = data.get('tree_path')
        
        if not session_id or not tree_path:
            return {"error": "Missing session_id or tree_path"}, 400
        
        user_id = get_user_id(user)
        
        conn = sqlite3.connect('database.sqlite')
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM session WHERE id = ? AND user_id = ?",
            (session_id, user_id)
        )
        
        if not cursor.fetchone():
            conn.close()
            return {"error": "Session not found or access denied"}, 403
        
        current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute(
            "UPDATE session SET lastTreeUserViewed = ?, lastChangeMade = ? WHERE id = ? AND user_id = ?",
            (tree_path, current_time, session_id, user_id)
        )
        
        conn.commit()
        conn.close()
        
        if debugging:
            print(f"Tree path saved for session {session_id}: {tree_path}")
        
        return {"success": True, "message": "Tree path saved successfully"}, 200
        
    except Exception as e:
        if debugging:
            print(f"Error saving tree path: {str(e)}")
        return {"error": f"Failed to save tree path: {str(e)}"}, 500

@app.route('/chatbot/get-tree-path', methods=['GET'])
def get_tree_path():
    try:
        user = get_current_user() or "guest"
        
        if user == "guest":
            return {"error": "Forbidden: Guest users cannot access tree paths."}, 403
        
        session_id = request.args.get('session')
        
        if not session_id:
            return {"error": "Missing session parameter"}, 400
        
        user_id = get_user_id(user)
        
        conn = sqlite3.connect('database.sqlite')
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT lastTreeUserViewed FROM session WHERE id = ? AND user_id = ?",
            (session_id, user_id)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {"error": "Session not found or access denied"}, 403
        
        tree_path = result[0]
        
        if debugging:
            print(f"Retrieved tree path for session {session_id}: {tree_path}")
        
        return {
            "tree_path": tree_path,
            "session_id": session_id
        }, 200
        
    except Exception as e:
        if debugging:
            print(f"Error retrieving tree path: {str(e)}")
        return {"error": f"Failed to retrieve tree path: {str(e)}"}, 500

@app.route('/update_session_title', methods=['POST'])
def update_session_title_route():
    try:
        user = get_current_user() or "guest"
        
        if user == "guest":
            if debugging:
                print("Guest user attempted to update session title")
            return {"error": "Forbidden: Guest users cannot update session titles."}, 403
        
        data = request.get_json() or {}
        session_id = data.get('session_id')
        new_title = data.get('title')
        
        if not session_id or not new_title:
            if debugging:
                print("Missing session_id or title in update request")
            return {"error": "Missing session_id or title"}, 400
        
        # Check if user owns the session
        if not is_session_owner(user, session_id):
            if debugging:
                print(f"User {user} is not authorized to update title for session: {session_id}")
            return {"error": "Forbidden: You do not have access to this session."}, 403
        
        # Update the session title
        success = update_session_title(session_id, new_title)
        
        if success:
            if debugging:
                print(f"Session title updated successfully for {session_id}: {new_title}")
            return {"success": True, "message": "Session title updated successfully"}, 200
        else:
            if debugging:
                print(f"Failed to update session title for {session_id}")
            return {"error": "Failed to update session title"}, 500
        
    except Exception as e:
        if debugging:
            print(f"Error updating session title: {str(e)}")
        return {"error": f"Failed to update session title: {str(e)}"}, 500

@app.route('/chatbot.html')
def chatbot_page():
    return render_template('chatbot.html')

if __name__ == '__main__':
    app.run(host=flaskIP, port=flaskPort, debug=flaskDebugging)