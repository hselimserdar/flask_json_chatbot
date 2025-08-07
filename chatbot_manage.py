
import datetime
import sqlite3
import os
from dotenv import load_dotenv
from gemini_api import call_gemini_api
from db_utilities import get_user_id, get_title_for_session, get_summary_for_session, get_summary_for_message_branch, get_message_connected_from, get_message_by_id

load_dotenv()
debugging = os.getenv("debugging", "false").lower() == "true"

def chat_with_gemini(username, message, session_id=None, first_message=False, parent_message_id=None):
    stateful = bool(username and session_id)
    user_id = get_user_id(username)

    if stateful:
        if first_message:
            first_prompt = [
                {"author": "user", "content": f"You are a helpful assistant. Please respond to this message: {message}\n\n"
                                              f"**FORMATTING GUIDELINES:**\n"
                                              f"- When displaying lists, use consistent bullet points (* or -)\n"
                                              f"- Each list item should be on its own line\n"
                                              f"- Use the same formatting style throughout your response\n"
                                              f"- Example format for lists:\n"
                                              f"* item 1\n"
                                              f"* item 2\n"
                                              f"* item 3"}
            ]
            try:
                reply = call_gemini_api(first_prompt, use_tools=True)

                summary_prompt = [
                    {"author": "user", "content": f"User asked: {message}"},
                    {"author": "assistant", "content": f"I responded: {reply}"},
                    {"author": "user", "content": "Create a comprehensive summary of this conversation that preserves ALL important information. Include:\n"
                                                  "1. **Personal Information**: User's name, preferences, interests, goals, or any personal details mentioned\n"
                                                  "2. **Tasks & Lists**: Shopping lists, to-do items, reminders, planned activities, or any lists the user created\n"
                                                  "3. **Ongoing Projects**: Work projects, creative endeavors, learning goals, or any multi-session activities\n"
                                                  "4. **Technical Details**: Code snippets, configurations, specific commands, or technical solutions\n"
                                                  "5. **Context & Preferences**: Preferred language, communication style, specific requirements mentioned\n"
                                                  "6. **Important Facts**: Key information, decisions made, or significant details that should be remembered\n\n"
                                                  "7. **Code**: Keep the last code if you answered with code to make adjustments on the next message.\n\n"
                                                  "Format the summary clearly with sections. This summary will be used as context for future messages, "
                                                  "so it's crucial that personal information like lists, tasks, and user preferences are preserved exactly."}
                ]
                summary = call_gemini_api(summary_prompt, use_tools=False)
                if debugging:
                    print("Summary result:", summary)
            except Exception as e:
                if debugging:
                    print("Error while calling Gemini API:", e)
                return None

            title_prompt = [
                {"author": "user", "content": f"Based on this conversation where user said: '{message}' "
                                              f"and I responded with: '{reply}', "
                                              f"give me a very short 3-5 word title. "
                                              f"Just return the title without quotes or extra text. "
                                              f"Answer in the same language as the user's message."}
            ]
            try:
                title_candidate = call_gemini_api(title_prompt, use_tools=False)
            except Exception as e:
                if debugging:
                    print("Error while calling Gemini API for title:", e)
                return None
                
            if debugging:
                print("Title candidate:", title_candidate)
            generated_title = (title_candidate or "New Conversation").strip().strip('"').strip('*')
            if debugging:
                print("Generated title:", generated_title)

            if message and reply and summary and generated_title:
                user_msg_id = add_message_to_session(session_id, "user", message, "", "main", "", 0)
                bot_msg_id = add_message_to_session(session_id, "bot", reply, summary, str(user_msg_id), "", 0)
                update_message_connections(user_msg_id, str(bot_msg_id))
                update_session_title(session_id, generated_title)
                
                user_message_data = get_message_by_id(user_msg_id)
                bot_message_data = get_message_by_id(bot_msg_id)
            else:
                if debugging:
                    print("Missing one of the required fields for message/session creation")
                    print(f"  message: {bool(message)} ('{message[:50] if message else 'None'}...')")
                    print(f"  reply: {bool(reply)} ('{reply[:50] if reply else 'None'}...')")
                    print(f"  summary: {bool(summary)} ('{summary[:50] if summary else 'None'}...')")
                    print(f"  generated_title: {bool(generated_title)} ('{generated_title}')")
                return None
            return {
                "session_id": session_id,
                "user_id": user_id,
                "title": generated_title,
                "messages": [
                    user_message_data or {"id": user_msg_id, "sender": "user", "content": message},
                    bot_message_data or {"id": bot_msg_id, "sender": "bot", "content": reply}
                ]
            }
        
        else:
            if parent_message_id:
                session_summary = get_summary_for_message_branch(parent_message_id)
            else:
                session_summary = get_summary_for_session(session_id)
            
            session_title = get_title_for_session(session_id)
            
            prompt = [
                {"author": "user", "content": f"**CONVERSATION CONTEXT**\n"
                                              f"Session Title: {session_title}\n\n"
                                              f"**Previous Conversation Summary:**\n{session_summary}\n\n"
                                              f"**Current User Message:** {message}\n\n"
                                              f"Please respond naturally to the current message while keeping all previous context in mind. "
                                              f"Pay special attention to any personal information, lists, tasks, or ongoing projects mentioned in the summary. "
                                              f"If the user references something from our previous conversation (like a shopping list, task, or personal detail), "
                                              f"acknowledge it and build upon it. Do not ask the user to repeat information that's already in the context.\n\n"
                                              f"**FORMATTING GUIDELINES:**\n"
                                              f"- When displaying lists, use consistent bullet points (- or *)\n"
                                              f"- Each list item should be on its own line\n"
                                              f"- Use the same formatting style throughout your response\n"
                                              f"- Example format for lists:\n"
                                              f"* item 1\n"
                                              f"* item 2\n"
                                              f"* item 3"}
            ]

            try:
                reply = call_gemini_api(prompt, use_tools=True)
                
                # Use branch-specific summary context when creating new summary
                if parent_message_id:
                    # For branches, use the parent message's summary as the base context
                    parent_summary = get_summary_for_message_branch(parent_message_id)
                    summary_context = f"Previous branch context: {parent_summary}\n"
                else:
                    # For regular conversation continuation, use session summary
                    summary_context = f"Previous context: {session_summary}\n"
                
                summary_prompt = [
                    {"author": "user", "content": f"Previous context: {summary_context}"
                                                  f"User just said: {message}\n"
                                                  f"I responded: {reply}\n\n"},
                    {"author": "user", "content": "Create a comprehensive summary of this conversation that preserves ALL important information. Include:\n"
                                                  "1. **Personal Information**: User's name, preferences, interests, goals, or any personal details mentioned\n"
                                                  "2. **Tasks & Lists**: Shopping lists, to-do items, reminders, planned activities, or any lists the user created\n"
                                                  "3. **Ongoing Projects**: Work projects, creative endeavors, learning goals, or any multi-session activities\n"
                                                  "4. **Technical Details**: Code snippets, configurations, specific commands, or technical solutions\n"
                                                  "5. **Context & Preferences**: Preferred language, communication style, specific requirements mentioned\n"
                                                  "6. **Important Facts**: Key information, decisions made, or significant details that should be remembered\n\n"
                                                  "7. **Code**: Keep the last code if you answered with code to make adjustments on the next message.\n\n"
                                                  "Format the summary clearly with sections. This summary will be used as context for future messages, "
                                                  "so it's crucial that personal information like lists, tasks, and user preferences are preserved exactly."}
                ]
                summary = call_gemini_api(summary_prompt, use_tools=False)
            except Exception as e:
                if debugging:
                    print("Error while calling Gemini API:", e)
                return None

            if session_title == "New Conversation":
                title_prompt = [
                    {"author": "user", "content": f"Based on this conversation summary: {summary}, "
                                                  f"give me a 3-5 word title. "
                                                  f"Just return the title without quotes or extra text."}
                ]
                try:
                    title_candidate = call_gemini_api(title_prompt, use_tools=False)
                    session_title = (title_candidate or "New Conversation").strip().strip('"').strip('*')
                    if session_title:
                        update_session_title(session_id, session_title)
                        if debugging:
                            print("Updated session title to:", session_title)
                except Exception as e:
                    if debugging:
                        print("Error while calling Gemini API for title:", e)

            if message and reply and summary:
                if parent_message_id:

                    if debugging:
                        print(f"Creating branch from parent bot message: {parent_message_id}")
                    
                    parent_bot_connected_from = get_message_connected_from(parent_message_id)
                    if parent_bot_connected_from:
                        if debugging:
                            print(f"Parent bot message {parent_message_id} was connected from: {parent_bot_connected_from}")

                        new_user_msg_id = add_message_to_session(session_id, "user", message, "", str(parent_message_id), "", 0)
                        
                        bot_msg_id = add_message_to_session(session_id, "bot", reply, summary, str(new_user_msg_id), "", 0)
                        
                        update_message_connections(parent_message_id, str(new_user_msg_id))
                        
                        update_message_connections(new_user_msg_id, str(bot_msg_id))
                        
                        if debugging:
                            print(f"Created branch: user {new_user_msg_id} -> bot {bot_msg_id}")
                        
                        user_message_data = get_message_by_id(new_user_msg_id)
                        bot_message_data = get_message_by_id(bot_msg_id)
                        parent_message_data = get_message_by_id(parent_message_id)
                        
                        return {
                            "session_id": session_id,
                            "user_id": user_id,
                            "title": session_title,
                            "messages": [
                                user_message_data or {"id": new_user_msg_id, "sender": "user", "content": message},
                                bot_message_data or {"id": bot_msg_id, "sender": "bot", "content": reply},
                                parent_message_data or {"id": parent_message_id, "sender": "bot", "content": ""}
                            ]
                        }
                    else:
                        if debugging:
                            print(f"Could not find connected_from for parent message {parent_message_id}")
                        return None
                else:

                    connected_from = get_last_message_id_for_session(session_id)
                    user_msg_id = add_message_to_session(session_id, "user", message, "", str(connected_from), "", 0)
                    bot_msg_id = add_message_to_session(session_id, "bot", reply, summary, str(user_msg_id), "", 0)
                    update_message_connections(connected_from, str(user_msg_id))
                    update_message_connections(user_msg_id, str(bot_msg_id))
                    
                    user_message_data = get_message_by_id(user_msg_id)
                    bot_message_data = get_message_by_id(bot_msg_id)
                    
                    return {
                        "session_id": session_id,
                        "user_id": user_id,
                        "title": session_title,
                        "messages": [
                            user_message_data or {"id": user_msg_id, "sender": "user", "content": message},
                            bot_message_data or {"id": bot_msg_id, "sender": "bot", "content": reply}
                        ]
                    }
            else:
                if debugging:
                    print("Missing one of the required fields for message/session creation")
                    print(f"  message: {bool(message)} ('{message[:50] if message else 'None'}...')")
                    print(f"  reply: {bool(reply)} ('{reply[:50] if reply else 'None'}...')")
                    print(f"  summary: {bool(summary)} ('{summary[:50] if summary else 'None'}...')")
                return None
    else:
        try:
            prompt = [{"author": "user", "content": message}]
            reply = call_gemini_api(prompt, use_tools=True)
            return {
                "session_id": "None",
                "user_id": "guest",
                "messages": [
                    {"id": "None", "sender": "user", "content": message},
                    {"id": "None", "sender": "bot", "content": reply}
                ]
            }
        except Exception as e:
            if debugging:
                print("Error while calling Gemini API:", e)
            return None

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
            "INSERT INTO session (user_id, title, isDeleted) VALUES (?, ?, ?)",
            (user_id, title, 'FALSE')
        )
        conn.commit()
        session_id = cur.lastrowid
        if debugging:
            print(
                f"Created session id={session_id} for username='{username}' "
                f"(user_id={user_id}) with isDeleted='FALSE'"
            )
        return session_id

    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in create_session_for_user:", e)
        return None

    finally:
        cur.close()
        conn.close()

def add_message_to_session(session_id, sender, content, summary, connected_from="", connects_to="", connections=0):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cur.execute(
            "INSERT INTO message (session_id, sender, content, summary, created_at, connected_from, connects_to, connections) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
            (session_id, sender, content, summary, created_at, connected_from, connects_to, connections)
        )
        row = cur.fetchone()
        conn.commit()
        message_id = row[0] if row else None
        if debugging:
            print(
                f"Inserted message id={message_id} in session_id={session_id}: "
                f"sender={sender}, content={content}, summary={summary}, at={created_at}, "
                f"connected_from={connected_from}, connects_to={connects_to}, connections={connections}"
            )
        return message_id
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in add_message_to_session:", e)
        return None
    finally:
        cur.close()
        conn.close()

def update_message_connections(message_id, new_connects_to_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute("SELECT connects_to, connections FROM message WHERE id = ?", (message_id,))
        row = cur.fetchone()
        if not row:
            if debugging:
                print(f"Message {message_id} not found for connection update")
            return False
        
        current_connects_to, current_connections = row
        
        if current_connects_to:
            new_connects_to = current_connects_to + "," + new_connects_to_id
        else:
            new_connects_to = new_connects_to_id
        
        new_connections = int(current_connections) + 1
        
        cur.execute(
            "UPDATE message SET connects_to = ?, connections = ? WHERE id = ?",
            (new_connects_to, new_connections, message_id)
        )
        conn.commit()
        
        if debugging:
            print(f"Updated message {message_id} connections: connects_to={new_connects_to}, connections={new_connections}")
        return cur.rowcount == 1
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in update_message_connections:", e)
        return False
    finally:
        cur.close()
        conn.close()

def get_last_message_id_for_session(session_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id FROM message WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
            (session_id,)
        )
        row = cur.fetchone()
        if row:
            if debugging:
                print(f"Last message id for session {session_id}: {row[0]}")
            return row[0]
        else:
            if debugging:
                print(f"No messages found for session {session_id}")
            return None
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in get_last_message_id_for_session:", e)
        return None
    finally:
        cur.close()
        conn.close()

def get_summary_for_message_branch(message_id):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute("SELECT summary FROM message WHERE id = ?", (message_id,))
        row = cur.fetchone()
        if row:
            summary = row[0]
            if debugging:
                print(f"Summary for message {message_id}: {summary}")
            return summary
        else:
            if debugging:
                print(f"No message found with id {message_id}")
            return None
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in get_summary_for_message_branch:", e)
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
