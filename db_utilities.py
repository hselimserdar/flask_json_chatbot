#db_utilities.py
import datetime
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

debugging = os.getenv("debugging", "false").lower() == "true"

def is_session_owner(username, session_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        if debugging:
            print(f"is_session_owner: Checking user '{username}' for session '{session_id}'")
        
        cur.execute("SELECT id FROM user WHERE username = ?", (username,))
        row = cur.fetchone()
        if not row:
            if debugging:
                print(f"is_session_owner: User '{username}' not found")
            return False
        user_id = row[0]
        if debugging:
            print(f"is_session_owner: Found user_id={user_id}")

        cur.execute(
            "SELECT user_id, isDeleted FROM session WHERE id = ?",
            (session_id,)
        )
        sess = cur.fetchone()
        if not sess:
            if debugging:
                print(f"is_session_owner: Session {session_id} not found")
            return False
        owner_id, is_deleted = sess
        if debugging:
            print(f"is_session_owner: Session {session_id} isDeleted={is_deleted}")

        if str(is_deleted).upper() == 'TRUE':
            if debugging:
                print(f"is_session_owner: session {session_id} is marked deleted")
            return False

        is_owner = (owner_id == user_id)
        if debugging:
            print(f"is_session_owner({username},{session_id}) -> {is_owner}")
        return is_owner

    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in is_session_owner:", e)
        return False
    finally:
        cur.close()
        conn.close()

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
    per_page = 9
    offset = (page - 1) * per_page

    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()

    try:
        cur.execute("SELECT id FROM user WHERE username = ?", (username,))
        row = cur.fetchone()
        user_id = row[0] if row else None

        if user_id is None:
            return {
                "meta": {"id": None, "username": username, "page": page,
                         "per_page": per_page, "total_sessions": 0},
                "sessions": [], "has_previous": False, "has_next": False
            }

        cur.execute(
            "SELECT COUNT(*) FROM session "
            "WHERE user_id = ? AND isDeleted = 'FALSE'",
            (user_id,)
        )
        total_sessions = cur.fetchone()[0]

        cur.execute(
            "SELECT id, title FROM session "
            "WHERE user_id = ? AND isDeleted = 'FALSE' "
            "ORDER BY id DESC LIMIT ? OFFSET ?",
            (user_id, per_page, offset)
        )
        session_rows = cur.fetchall()

        sessions = []
        for sid, title in session_rows:
            sessions.append({
                "id": sid,
                "user_id": user_id,
                "title": title,
                "created_at": get_created_at_for_session(sid)
            })

        has_previous = page > 1
        has_next = (offset + per_page) < total_sessions

        result = {
            "meta": {
                "id": user_id,
                "username": username,
                "page": page,
                "per_page": per_page,
                "total_sessions": total_sessions
            },
            "sessions": sessions,
            "has_previous": has_previous,
            "has_next": has_next,
        }

        if debugging:
            print(f"print_sessions({username}) ->", result)
        return result

    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in print_sessions:", e)
        return {
            "meta": {"id": user_id, "username": username, "page": page,
                     "per_page": per_page, "total_sessions": 0},
            "sessions": [], "has_previous": False, "has_next": False
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
            "SELECT rowid, sender, content, created_at "
            "FROM message "
            "WHERE session_id = ? "
            "ORDER BY created_at",
            (session_id,)
        )
        rows = cur.fetchall()

        messages = []
        for msg_id, sender, content, created_at in rows:
            if isinstance(created_at, datetime.datetime):
                created_at = created_at.isoformat()
            messages.append({
                'id':         msg_id,
                'session_id': session_id,
                'user_id':    user_id,
                'sender':     sender,
                'content':    content,
                'created_at': created_at
            })

        if debugging:
            print(f"Fetched {len(messages)} messages for session_id={session_id}")
        return {'data': messages}

    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in get_messages_for_session:", e)
        return {'data': []}

    finally:
        cur.close()
        conn.close()

def delete_session_for_user(username, session_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM user WHERE username = ?", (username,))
        row = cur.fetchone()
        if not row:
            if debugging:
                print(f"delete_session_for_user: user '{username}' not found")
            return False
        user_id = row[0]

        cur.execute(
            "UPDATE session "
            "SET isDeleted = 'TRUE' "
            "WHERE id = ? AND user_id = ?",
            (session_id, user_id)
        )
        conn.commit()

        if cur.rowcount != 1:
            if debugging:
                print(
                    f"delete_session_for_user: no session marked deleted "
                    f"(session_id={session_id}, user_id={user_id})"
                )
            return False

        if debugging:
            print(
                f"delete_session_for_user: marked session_id={session_id} "
                f"as deleted for user_id={user_id}"
            )
        return True

    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in delete_session_for_user:", e)
        return False

    finally:
        cur.close()
        conn.close()

def remove_invalid_sessions():
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM session WHERE isDeleted = TRUE"
        )
        removed_count = cur.rowcount
        conn.commit()
        if debugging:
            print(f"remove_invalid_sessions: permanently deleted {removed_count} sessions")
        return removed_count
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in remove_invalid_sessions:", e)
        return 0
    finally:
        cur.close()
        conn.close()