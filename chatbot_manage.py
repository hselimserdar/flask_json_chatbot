#chatbot_manage.py
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
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cur.execute(
            "INSERT INTO message (session_id, sender, content, summary, created_at) "
            "VALUES (?, ?, ?, ?, ?) RETURNING id",
            (session_id, sender, content, summary, created_at)
        )
        row = cur.fetchone()
        conn.commit()
        message_id = row[0] if row else None
        if debugging:
            print(
                f"Inserted message id={message_id} in session_id={session_id}: "
                f"sender={sender}, content={content}, summary={summary}, at={created_at}"
            )
        return message_id
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in add_message_to_session:", e)
        return None
    finally:
        cur.close()
        conn.close()

def print_sessions(username, page):
    if page is None or page < 1:
        page = 1
    pagination_count = 25
    offset = (page - 1) * pagination_count

    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()

    try:
        cur.execute("SELECT id FROM user WHERE username = ?", (username,))
        row = cur.fetchone()
        user_id = row[0] if row else None

        if user_id is None:
            result = {
                "user": {"id": None, "username": username},
                "sessions": [],
                "page": page,
                "per_page": pagination_count,
                "total_sessions": 0,
            }
            if debugging:
                print(f"print_sessions({username}) ->", result)
            return result

        cur.execute("SELECT COUNT(*) FROM session WHERE user_id = ?", (user_id,))
        total_sessions = cur.fetchone()[0]

        cur.execute(
            "SELECT id, title FROM session WHERE user_id = ? ORDER BY id ASC LIMIT ? OFFSET ?",
            (user_id, pagination_count, offset),
        )
        session_rows = cur.fetchall()
        sessions = []
        for sid, title in session_rows:
            sessions.append({"id": sid, "user_id": user_id, "title": title})

        result = {
            "meta": {"id": user_id, "username": username, "page": page, "per_page": pagination_count, "total_sessions": total_sessions},
            "sessions": sessions,
        }

        if debugging:
            print(f"print_sessions({username}) ->", result)
        return result

    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in print_sessions:", e)
        return {
            "user": {"id": user_id if 'user_id' in locals() else None, "username": username},
            "sessions": [],
            "page": page,
            "per_page": pagination_count,
            "total_sessions": 0,
        }

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

def get_user_id(username):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM user WHERE username = ?", (username,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        cur.close()
        conn.close()

def chat_with_gemini(username, message, session_id=None, first_message=False):
    stateful = bool(username and session_id)
    user_id = get_user_id(username)

    if stateful:
        if first_message:
            first_prompt = [
                {"author": "system",    "content": "You are a helpful assistant."},
                {"author": "user",      "content": "Prompt: " + message}
            ]
            try:
                reply = call_gemini_api(first_prompt)

                first_prompt.append({"author": "assistant", "content": "GPT Answer: " + reply})
                first_prompt.append({
                    "author": "system",
                    "content": "Give me the summary of this conversation so far. "
                               "Do not skip important details while keeping it concise."
                               "Especially technical details, if exists."
                               "Also put the preferred language in the summary if it is mentioned in the conversation."
                               "I will use this as context for the next message."
                })
                summary = call_gemini_api(first_prompt)
            except Exception as e:
                if debugging:
                    print("Error while calling Gemini API:", e)
                return None

            title_prompt = [
                {"author": "system",
                 "content": "Give me a very short (3-5 word) title summarizing this conversation so far."
                 "Just return the title without any additional text. It should be concise and descriptive."
                 "Do not go beyond 5 words. Do not use quotes or any other punctuation. Do not use 'title' in the response."
                 "Do not use any special characters or formatting. Just 3 to 5 plain words."},
                {"author": "assistant", "content": "GPT Conversation Summary: " + summary}
            ]
            try:
                title_candidate = call_gemini_api(title_prompt)
            except Exception as e:
                if debugging:
                    print("Error while calling Gemini API for title:", e)
                return None
            if debugging:
                print("Title candidate:", title_candidate)
            generated_title = (title_candidate or "New Conversation").strip().strip('"').strip('*')
            if debugging:
                print("Generated title:", generated_title)

            user_msg_id = add_message_to_session(session_id, "user", message, "")
            bot_msg_id  = add_message_to_session(session_id, "bot",  reply,   summary)

            update_session_title(session_id, generated_title)

            return {
                "session_id": session_id,
                "user_id":    user_id,
                "title": generated_title,
                "messages": [
                    {"message_id": user_msg_id, "sender": "user", "content": message},
                    {"message_id": bot_msg_id,  "sender": "bot",  "content": reply}
                ]
            }
        
        else:
            session_title = get_title_for_session(session_id)
            prompt = [
                {"author": "system",
                 "content": "These are the summary and title so far. Use them "
                            "and the following message as context for the next reply."
                            "Do not repeat the summary or title in your reply."
                            "Do not say 'based on the title and summary' and/or refer to the summary."
                            "Do not say given the context or anything similar. Unless the user asks for it, do not repeat the summary or title."
                            "Answer in the language of the user's preference, if it is mentioned."
                            "This will be used as context for the next message as follow-up."},
                {"author": "assistant", "content": "Title: " + session_title},
                {"author": "assistant", "content": "Summary so far: " + get_summary_for_session(session_id)},
                {"author": "user",      "content": "Prompt: " + message}
            ]

            try:
                reply = call_gemini_api(prompt)
                prompt.append({"author": "assistant", "content": "GPT Answer: " + reply})
                prompt.append({
                    "author": "system",
                    "content": "Give me the summary of this conversation so far. "
                               "It includes old summary, title, your last reply, and the new user message."
                               "Do not skip important details while keeping it concise."
                               "Especially technical details, if exists."
                               "Also put the preferred language in the summary if it is mentioned in the conversation."
                               "I will use this as context for the next message."
                })
                summary = call_gemini_api(prompt)
            except Exception as e:
                if debugging:
                    print("Error while calling Gemini API:", e)
                return None

            if session_title == "New Conversation":
                title_prompt = [
                    {"author": "system",
                    "content": "Give me a very short (3-5 word) title summarizing this conversation so far."
                    "Just return the title without any additional text. It should be concise and descriptive."
                    "Do not go beyond 5 words. Do not use quotes or any other punctuation. Do not use 'title' in the response."
                    "Do not use any special characters or formatting. Just 3 to 5 plain words."},
                    {"author": "assistant", "content": "GPT Conversation Summary: " + summary}
                ]
                try:
                    title_candidate = call_gemini_api(title_prompt)
                except Exception as e:
                    if debugging:
                        print("Error while calling Gemini API for title:", e)
                    return None
                if debugging:
                    print("Title candidate:", title_candidate)
                session_title = (title_candidate or "New Conversation").strip().strip('"').strip('*')
                if debugging:
                    print("Generated title:", session_title)
                update_session_title(session_id, session_title)

            user_msg_id = add_message_to_session(session_id, "user", message, "")
            bot_msg_id  = add_message_to_session(session_id, "bot",  reply,   summary)

            return {
                "session_id": session_id,
                "user_id":    user_id,
                "title":     session_title,
                "messages": [
                    {"message_id": user_msg_id, "sender": "user", "content": message},
                    {"message_id": bot_msg_id,  "sender": "bot",  "content": reply}
                ]
            }
    else:
        try:
            reply = call_gemini_api([{"author": "user", "content": message}])
            return {
                "session_id": "None",
                "user_id":    "guest",
                "messages": [
                    {"message_id": "None", "sender": "user", "content": message},
                    {"message_id": "None",  "sender": "bot",  "content": reply}
                ]
            }
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
        cur.execute("SELECT user_id FROM session WHERE id = ?", (session_id,))
        row = cur.fetchone()
        user_id = row[0] if row else None

        cur.execute(
            "SELECT id, sender, content, created_at "
            "FROM message "
            "WHERE session_id = ? "
            "ORDER BY created_at",
            (session_id,)
        )
        rows = cur.fetchall()

        messages = []
        for id, sender, content, created_at in rows:
            if isinstance(created_at, (datetime.datetime,)):
                created_at = created_at.isoformat()
            messages.append({
                'id': id,
                'session_id': session_id,
                'user_id': user_id,
                'sender': sender,
                'content': content,
                'created_at': created_at
            })

        if debugging:
            print(f"Fetched {len(messages)} messages for session_id={session_id}")
        return {"data": messages}
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in get_messages_for_session:", e)
        return {"data": []}
    finally:
        cur.close()
        conn.close()