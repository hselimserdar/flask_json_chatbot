
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
    per_page = 15
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
            "ORDER BY lastChangeMade DESC, id DESC LIMIT ? OFFSET ?",
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
            "WHERE session_id = ? AND summary != '' "
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
                print(f"No messages with summary found for session_id={session_id}")
            return None
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in get_summary_for_session:", e)
        return None
    finally:
        cur.close()
        conn.close()

def get_summary_for_message_branch(message_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT summary FROM message "
            "WHERE id = ? AND summary != ''",
            (message_id,)
        )
        row = cur.fetchone()
        if row:
            summary = row[0]
            if debugging:
                print(f"Summary for message_id={message_id}: {summary}")
            return summary
        else:
            if debugging:
                print(f"No summary found for message_id={message_id}")
            return None
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in get_summary_for_message_branch:", e)
        return None
    finally:
        cur.close()
        conn.close()

def get_message_branch_info(session_id, message_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT connected_to, connections FROM message "
            "WHERE session_id = ? AND id = ?",
            (session_id, message_id)
        )
        row = cur.fetchone()
        if row:
            connected_to, connections = row
            branch_ids = connected_to.split(',') if connected_to else []
            if debugging:
                print(f"Message {message_id} has {connections} connections: {branch_ids}")
            return {
                'connected_to': connected_to,
                'connections': connections,
                'branch_ids': branch_ids
            }
        else:
            if debugging:
                print(f"Message {message_id} not found in session {session_id}")
            return None
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in get_message_branch_info:", e)
        return None
    finally:
        cur.close()
        conn.close()

def get_message_by_id(message_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, session_id, sender, content, created_at, connected_from, connects_to, connections "
            "FROM message WHERE id = ?",
            (message_id,)
        )
        row = cur.fetchone()
        if row:
            msg_id, session_id, sender, content, created_at, connected_from, connects_to, connections = row
            if isinstance(created_at, datetime.datetime):
                created_at = created_at.isoformat()
            
            message_data = {
                'id': msg_id,
                'session_id': session_id,
                'sender': sender,
                'content': content,
                'created_at': created_at,
                'connected_from': connected_from,
                'connects_to': connects_to,
                'connections': connections
            }
            if debugging:
                print(f"Retrieved message {message_id}: {message_data}")
            return message_data
        else:
            if debugging:
                print(f"Message {message_id} not found")
            return None
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in get_message_by_id:", e)
        return None
    finally:
        cur.close()
        conn.close()

def get_messages_for_session(session_id, tree_path=None):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id FROM session WHERE id = ?", (session_id,))
        row = cur.fetchone()
        user_id = row[0] if row else None

        messages = get_all_session_messages(session_id, cur)

        if debugging:
            print(f"Fetched {len(messages)} messages for session_id={session_id}, tree_path={tree_path}")
        return {'data': messages}

    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in get_messages_for_session:", e)
        return {'data': []}

    finally:
        cur.close()
        conn.close()

def get_all_session_messages(session_id, cur):
    cur.execute(
        "SELECT id, sender, content, created_at, connected_from, connects_to, connections "
        "FROM message "
        "WHERE session_id = ? "
        "ORDER BY created_at",
        (session_id,)
    )
    rows = cur.fetchall()
    
    messages = []
    for row in rows:
        messages.append(format_message(row, session_id))
    
    if debugging:
        print(f"get_all_session_messages: Found {len(messages)} total messages for session {session_id}")
    
    return messages

def get_main_branch_messages(session_id, cur):
    messages = []
    
    cur.execute(
        "SELECT id, sender, content, created_at, connected_from, connects_to, connections "
        "FROM message "
        "WHERE session_id = ? AND connected_from = 'main' "
        "ORDER BY created_at",
        (session_id,)
    )
    root_messages = cur.fetchall()
    
    if not root_messages:
        if debugging:
            print(f"No root messages found for session {session_id}")
        return messages
    
    current_message = root_messages[0]
    messages.append(format_message(current_message, session_id))
    
    while True:
        msg_id, sender, content, created_at, connected_from, connects_to, connections = current_message
        
        if not connects_to:
            break
            
        next_message_ids = connects_to.split(',')
        if not next_message_ids or not next_message_ids[0]:
            break
            
        next_message_id = next_message_ids[0]
        
        cur.execute(
            "SELECT id, sender, content, created_at, connected_from, connects_to, connections "
            "FROM message "
            "WHERE id = ?",
            (next_message_id,)
        )
        next_row = cur.fetchone()
        
        if not next_row:
            if debugging:
                print(f"Next message {next_message_id} not found")
            break
            
        messages.append(format_message(next_row, session_id))
        current_message = next_row
    
    return messages

def get_branch_messages(session_id, tree_path, cur):
    messages = []
    tree_ids = tree_path.split(',')
    
    if debugging:
        print(f"Following tree path: {tree_ids}")
    
    cur.execute(
        "SELECT id, sender, content, created_at, connected_from, connects_to, connections "
        "FROM message "
        "WHERE session_id = ? AND connected_from = 'main' "
        "ORDER BY created_at",
        (session_id,)
    )
    root_messages = cur.fetchall()
    
    if not root_messages:
        if debugging:
            print(f"No root messages found for session {session_id}")
        return messages
    
    current_message = root_messages[0]
    messages.append(format_message(current_message, session_id))
    
    tree_index = 0
    
    while tree_index < len(tree_ids) and tree_ids[tree_index]:
        target_id = tree_ids[tree_index]
        msg_id, sender, content, created_at, connected_from, connects_to, connections = current_message
        
        cur.execute(
            "SELECT id, sender, content, created_at, connected_from, connects_to, connections "
            "FROM message "
            "WHERE id = ?",
            (target_id,)
        )
        next_row = cur.fetchone()
        
        if not next_row:
            if debugging:
                print(f"Target message {target_id} not found in database")
            break
        
        next_id, next_sender, next_content, next_created_at, next_connected_from, next_connects_to, next_connections = next_row
        
        if next_connected_from != str(msg_id) and next_connected_from != 'main':

            cur.execute(
                "SELECT id FROM message WHERE connects_to LIKE ? OR connects_to LIKE ? OR connects_to LIKE ? OR connects_to = ?",
                (f"{target_id},%", f"%,{target_id},%", f"%,{target_id}", target_id)
            )
            connecting_messages = cur.fetchall()
            
            if not any(str(row[0]) == str(msg_id) for row in connecting_messages):
                if debugging:
                    print(f"Target message {target_id} is not properly connected to message {msg_id}")

        messages.append(format_message(next_row, session_id))
        current_message = next_row
        tree_index += 1
    
    while True:
        msg_id, sender, content, created_at, connected_from, connects_to, connections = current_message
        
        if not connects_to:
            break
            
        next_message_ids = connects_to.split(',')
        if not next_message_ids or not next_message_ids[0]:
            break
            
        next_message_id = next_message_ids[0]
        
        cur.execute(
            "SELECT id, sender, content, created_at, connected_from, connects_to, connections "
            "FROM message "
            "WHERE id = ?",
            (next_message_id,)
        )
        next_row = cur.fetchone()
        
        if not next_row:
            if debugging:
                print(f"Next message {next_message_id} not found")
            break
            
        messages.append(format_message(next_row, session_id))
        current_message = next_row
    
    return messages

def format_message(message_row, session_id):
    msg_id, sender, content, created_at, connected_from, connects_to, connections = message_row
    
    if isinstance(created_at, datetime.datetime):
        created_at = created_at.isoformat()
    
    return {
        'id': msg_id,
        'session_id': session_id,
        'sender': sender,
        'content': content,
        'created_at': created_at,
        'connected_from': connected_from,
        'connects_to': connects_to,
        'connections': connections
    }

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

def get_session_id_for_message(message_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute("SELECT session_id FROM message WHERE id = ?", (message_id,))
        row = cur.fetchone()
        if row:
            if debugging:
                print(f"Message {message_id} belongs to session {row[0]}")
            return row[0]
        else:
            if debugging:
                print(f"No message found with id={message_id}")
            return None
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in get_session_id_for_message:", e)
        return None
    finally:
        cur.close()
        conn.close()

def update_session_last_change(session_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cur.execute(
            "UPDATE session SET lastChangeMade = ? WHERE id = ?",
            (current_time, session_id)
        )
        conn.commit()
        if debugging:
            print(f"Updated lastChangeMade for session {session_id} to {current_time}")
        return cur.rowcount == 1
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in update_session_last_change:", e)
        return False
    finally:
        cur.close()
        conn.close()

def initialize_missing_last_change_timestamps():
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT s.id, MIN(m.created_at) as first_message_time
            FROM session s
            LEFT JOIN message m ON s.id = m.session_id
            WHERE s.lastChangeMade IS NULL AND s.isDeleted = 'FALSE'
            GROUP BY s.id
        """)
        sessions_to_update = cur.fetchall()
        
        updated_count = 0
        for session_id, first_message_time in sessions_to_update:
            timestamp = first_message_time or datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            cur.execute(
                "UPDATE session SET lastChangeMade = ? WHERE id = ?",
                (timestamp, session_id)
            )
            updated_count += 1
        
        conn.commit()
        if debugging:
            print(f"Initialized lastChangeMade for {updated_count} sessions")
        return updated_count
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in initialize_missing_last_change_timestamps:", e)
        return 0
    finally:
        cur.close()
        conn.close()

def get_message_connected_from(message_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute("SELECT connected_from FROM message WHERE id = ?", (message_id,))
        row = cur.fetchone()
        if row:
            connected_from = row[0]
            if debugging:
                print(f"Message {message_id} connected_from: {connected_from}")
            return connected_from
        else:
            if debugging:
                print(f"No message found with id={message_id}")
            return None
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in get_message_connected_from:", e)
        return None
    finally:
        cur.close()
        conn.close()