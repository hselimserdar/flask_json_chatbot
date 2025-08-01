import datetime
import sqlite3
import os
from dotenv import load_dotenv
from gemini_api import call_gemini_api

load_dotenv()
debugging = os.getenv("debugging", "false").lower() == "true"

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

def add_message_to_session(session_id, sender, content, summary):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        created_at = datetime.datetime.now(datetime.timezone.utc)
        cur.execute(
            "INSERT INTO message (session_id, sender, content, summary, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, sender, content, summary, created_at)
        )
        conn.commit()
        if debugging:
            print(
                f"Inserted message in session_id={session_id}: "
                f"sender={sender}, content={content}, summary={summary}, at={created_at}"
            )
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

def chat_with_gemini(username, message, session_id=None, first_message=False):
    stateful = bool(username and session_id and is_session_owner(username, session_id))

    if stateful:
        if first_message:
            first_prompt = [
                {"author": "system",    "content": "You are a helpful assistant."},
                {"author": "user",      "content": message}
            ]
            try:
                reply = call_gemini_api(first_prompt)

                first_prompt.append({"author": "assistant", "content": reply})
                first_prompt.append({
                    "author": "system",
                    "content": "Give me the summary of this conversation so far. "
                               "I will use this as context for the next message."
                })
                summary = call_gemini_api(first_prompt)
            except Exception as e:
                if debugging:
                    print("Error while calling Gemini API:", e)
                return None

            title_prompt = [
                {"author": "system",
                 "content": "Give me a very short (3-5 word) title summarizing this conversation so far."},
                {"author": "assistant", "content": summary}
            ]
            try:
                title_candidate = call_gemini_api(title_prompt)
            except Exception as e:
                if debugging:
                    print("Error while calling Gemini API for title:", e)
                return None

            generated_title = (title_candidate or "New Conversation").strip().strip('"')

            add_message_to_session(session_id, "user", message, summary)
            add_message_to_session(session_id, "bot", reply, summary)
            update_session_title(session_id, generated_title)
            return reply

        else:
            prompt = [
                {"author": "system",
                 "content": "These are the summary and title so far. Use them "
                            "and the following message as context for the next reply."},
                {"author": "assistant", "content": "Title: " + get_title_for_session(session_id)},
                {"author": "assistant", "content": "Summary: " + get_summary_for_session(session_id)},
                {"author": "user",      "content": "Message: " + message}
            ]

            try:
                reply = call_gemini_api(prompt)
                prompt.append({"author": "assistant", "content": reply})
                prompt.append({
                    "author": "system",
                    "content": "Give me the summary of this conversation so far. "
                               "It includes old summary, title, your last reply, and the new user message."
                })
                summary = call_gemini_api(prompt)
            except Exception as e:
                if debugging:
                    print("Error while calling Gemini API:", e)
                return None

            add_message_to_session(session_id, "user",    message, summary)
            add_message_to_session(session_id, "bot",     reply,   summary)
            return reply

    else:
        try:
            reply = call_gemini_api([{"author": "user", "content": message}])
            return reply
        except Exception as e:
            if debugging:
                print("Error while calling Gemini API:", e)
            return None
        
def get_title_for_session(session_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute("SELECT title FROM session WHERE id = ?", (session_id,))
        row = cur.fetchone()
        if row:
            if debugging:
                print(f"Fetched title for session {session_id}: {row[0]}")
            return row[0]
        else:
            if debugging:
                print(f"No session found with id={session_id}")
            return None
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in get_title_for_session:", e)
        return None
    finally:
        cur.close()
        conn.close()

def get_summary_for_session(session_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT summary FROM message "
            "WHERE session_id = ? "
            "ORDER BY created_at DESC "
            "LIMIT 1",
            (session_id,)
        )
        row = cur.fetchone()
        if row:
            summary = row[0]
            if debugging:
                print(f"Latest summary for session_id={session_id}: {summary}")
            return summary
        else:
            if debugging:
                print(f"No messages found for session_id={session_id}")
            return None
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in get_summary_for_session:", e)
        return None
    finally:
        cur.close()
        conn.close()

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
            {
                'sender': sender,
                'content': content,
                'created_at': created_at
            }
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
    if session_id is None:
        session_id = "guest"
    return {
        " user": message,
        "chatbot": reply,
        "session_id": session_id
    }