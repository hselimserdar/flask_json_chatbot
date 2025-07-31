import datetime
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
debugging = os.getenv("debugging", "false").lower() == "true"

def call_gemini_api(conversation):
    
    if debugging:
        print("Calling Gemini API with conversation:", conversation)
    return "This is a mock response from Gemini API."

def create_session_for_user(username, title=None):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM user WHERE username = ?", (username,))
        row = cur.fetchone()
        if not row:
            if debugging:
                print(f"User '{username}' not found; cannot create session.")
            return None
        user_id = row[0]

        cur.execute(
            "INSERT INTO session (user_id, title) VALUES (?, ?)",
            (user_id, title)
        )
        conn.commit()

        session_id = cur.lastrowid
        if debugging:
            print(f"Created session id={session_id} for username='{username}' (user_id={user_id})")
        return session_id

    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in create_session_for_user:", e)
        return None

    finally:
        cur.close()
        conn.close()

def add_message_to_session(session_id, sender, content):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        created_at = datetime.datetime.now(datetime.timezone.utc)
        cur.execute(
            "INSERT INTO message (session_id, sender, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, sender, content, created_at)
        )
        conn.commit()
        if debugging:
            print(f"Inserted message in session_id={session_id}: sender={sender}, content={content}, at={created_at}")
        return True
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in add_message_to_session:", e)
        return False
    finally:
        cur.close()
        conn.close()

def list_session_ids_for_user(username):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM user WHERE username = ?", (username,))
        row = cur.fetchone()
        if not row:
            if debugging:
                print(f"User '{username}' not found; no sessions to list.")
            return []
        user_id = row[0]

        cur.execute("SELECT id FROM session WHERE user_id = ?", (user_id,))
        rows = cur.fetchall()
        session_ids = [r[0] for r in rows]

        if debugging:
            print(f"Session IDs for username='{username}': {session_ids}")
            if not session_ids:
                print(f"No sessions found for user '{username}'")
        return session_ids

    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in list_session_ids_for_user:", e)
        return []
    finally:
        cur.close()
        conn.close()

def print_sessions(username):
    session_ids = list_session_ids_for_user(username)
    sessions = []

    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        for session_id in session_ids:
            cur.execute("SELECT title FROM session WHERE id = ?", (session_id,))
            row = cur.fetchone()
            title = row[0] if row else None
            sessions.append({"session_id": session_id, "title": title})

        if debugging:
            print(f"print_sessions({username}) -> {sessions}")
        return sessions

    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in print_sessions:", e)
        return []

    finally:
        cur.close()
        conn.close()

def is_session_owner(username, session_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM user WHERE username = ?", (username,))
        user_row = cur.fetchone()
        if not user_row:
            return False
        user_id = user_row[0]

        cur.execute("SELECT user_id FROM session WHERE id = ?", (session_id,))
        sess_row = cur.fetchone()
        return bool(sess_row and sess_row[0] == user_id)
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in is_session_owner:", e)
    finally:
        cur.close()
        conn.close()

def chat_with_gemini(username, message, session_id=None):
    stateful = bool(username and session_id and is_session_owner(username, session_id))
    history = get_messages_for_session(session_id) if stateful else []

    convo = []
    for msg in history:
        convo.append({"author": msg["sender"], "content": msg["content"]})

    convo.append({"author": "user", "content": message})

    reply = call_gemini_api(convo)

    if stateful and not history:
        title_prompt = [
            {"author": "system", "content": "Give me a very short (3–5 word) title summarizing this conversation so far."},
            {"author": "bot",    "content": reply}
        ]
        generated_title = call_gemini_api(title_prompt).strip().strip('"')
        update_session_title(session_id, generated_title)

    if stateful:
        add_message_to_session(session_id, "user", message)
        add_message_to_session(session_id, "bot", reply)

    return reply

def update_session_title(session_id, new_title):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE session SET title = ? WHERE id = ?",
            (new_title, session_id)
        )
        conn.commit()
        if debugging:
            print(f"Updated session {session_id} title to: {new_title}")
        return cur.rowcount == 1
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in update_session_title:", e)
        return False
    finally:
        cur.close()
        conn.close()

def get_messages_for_session(session_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT sender, content, created_at "
            "FROM message "
            "WHERE session_id = ? "
            "ORDER BY created_at",
            (session_id,)
        )
        rows = cur.fetchall()
        messages = [
            {'sender': sender, 'content': content, 'created_at': created_at}
            for sender, content, created_at in rows
        ]
        if debugging:
            print(f"Fetched {len(messages)} messages for session_id={session_id}")
        return messages
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in get_messages_for_session:", e)
        return []
    finally:
        cur.close()
        conn.close()

def handle_message(session_id, message, reply):
    return {
        " user": message,
        "chatbot": reply,
        "session_id": session_id
    }