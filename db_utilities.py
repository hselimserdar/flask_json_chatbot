#db_utilities.py
import datetime
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

debugging = os.getenv("debugging", "false").lower() == "true"

def get_created_at_for_session(session_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT created_at FROM message "
            "WHERE session_id = ? "
            "ORDER BY created_at ASC "
            "LIMIT 1",
            (session_id,)
        )
        row = cur.fetchone()
        if row:
            if debugging:
                print(f"First message for session_id={session_id} created at: {row[0]}")
            return row[0]
        else:
            if debugging:
                print(f"No messages found for session_id={session_id}")
            return None
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in get_created_at_for_session:", e)
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
            sessions.append({"id": sid, "user_id": user_id, "title": title, "created_at": get_created_at_for_session(sid)})

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